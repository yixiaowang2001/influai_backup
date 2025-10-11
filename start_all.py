#!/usr/bin/env python3
"""
InfluAI 完整系统启动脚本
一键启动所有必要的服务：Redis、Celery Worker、FastAPI主服务
"""
import os
import sys
import time
import signal
import subprocess
import argparse
import logging
import socket
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置基础日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 导入增强日志管理器
try:
    from backend.utils.enhanced_logger import LogEvents, get_enhanced_logger
    enhanced_logging_available = True
    app_logger = get_enhanced_logger("app")
except ImportError:
    enhanced_logging_available = False
    app_logger = logger

# 全局进程管理器
class ProcessManager:
    """进程管理器：负责注册和优雅关闭所有子进程"""
    
    def __init__(self):
        self.processes = []
        
    def register_process(self, process, name):
        """注册需要管理的进程"""
        self.processes.append({
            'process': process,
            'name': name,
            'start_time': time.time()
        })
        logger.info(f"已注册进程: {name} (PID: {process.pid})")
        
    def graceful_shutdown_all(self):
        """优雅关闭所有注册的进程"""
        if not self.processes:
            logger.info("没有需要关闭的进程")
            return
            
        logger.info(f"开始优雅关闭 {len(self.processes)} 个进程...")
        
        for proc_info in self.processes:
            process = proc_info['process']
            name = proc_info['name']
            
            if process.poll() is None:  # 进程仍在运行
                logger.info(f"正在关闭 {name}...")
                
                try:
                    # 第一步：发送 SIGTERM 信号（优雅关闭）
                    process.terminate()
                    
                    # 第二步：等待进程自行退出（给5秒时间）
                    process.wait(timeout=5)
                    logger.info(f"✓ {name} 已优雅关闭")
                    
                except subprocess.TimeoutExpired:
                    # 第三步：如果5秒内没有退出，强制关闭
                    logger.warning(f"⚠️ {name} 未能在5秒内退出，强制关闭")
                    process.kill()
                    process.wait()  # 确保进程完全退出
                    logger.info(f"✓ {name} 已强制关闭")
                    
                except Exception as e:
                    logger.error(f"关闭 {name} 时出错: {e}")
            else:
                logger.info(f"{name} 已经停止运行")
        
        self.processes.clear()
        logger.info("所有进程已关闭")

# 全局进程管理器实例
process_manager = ProcessManager()

def log_service_event(service_name, event, details=None, level="info"):
    """统一的服务事件日志记录"""
    message = f"{service_name}: {event}"
    if details:
        message += f" - {details}"
    
    # 同时记录到控制台和文件
    if level == "error":
        logger.error(message)
        if enhanced_logging_available:
            LogEvents.service_status(service_name, "error", details)
    elif level == "warning":
        logger.warning(message)
        if enhanced_logging_available:
            LogEvents.service_status(service_name, "warning", details)
    else:
        logger.info(message)
        if enhanced_logging_available:
            LogEvents.service_status(service_name, event, details)

def is_port_available(port):
    """检查端口是否可用"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except OSError:
        return False

def find_available_port(start_port=3000, max_attempts=10):
    """智能寻找可用端口"""
    for port in range(start_port, start_port + max_attempts):
        if is_port_available(port):
            return port
    return None

def cleanup_port_processes(ports):
    """清理指定端口上的进程"""
    for port in ports:
        try:
            # 查找占用端口的进程
            result = subprocess.run(
                ['lsof', '-ti', f':{port}'], 
                capture_output=True, text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    try:
                        # 尝试优雅关闭
                        logger.info(f"发现端口 {port} 被进程 {pid} 占用，尝试优雅关闭...")
                        subprocess.run(['kill', '-TERM', pid], capture_output=True, timeout=2)
                        time.sleep(2)
                        
                        # 检查进程是否还在运行
                        check_result = subprocess.run(['kill', '-0', pid], capture_output=True)
                        if check_result.returncode == 0:
                            # 进程仍在运行，强制关闭
                            logger.warning(f"进程 {pid} 未能优雅关闭，强制终止")
                            subprocess.run(['kill', '-KILL', pid], capture_output=True)
                        
                        logger.info(f"✓ 已清理端口 {port} 上的进程 {pid}")
                        
                    except subprocess.TimeoutExpired:
                        logger.warning(f"清理进程 {pid} 超时")
                    except ProcessLookupError:
                        # 进程已不存在
                        pass
                    except Exception as e:
                        logger.error(f"清理进程 {pid} 时出错: {e}")
                        
        except Exception as e:
            logger.warning(f"清理端口 {port} 时出现警告: {e}")

def cleanup_frontend_processes():
    """清理前端相关进程"""
    logger.info("清理前端服务器进程...")
    
    # 方法1: 根据端口清理
    cleanup_port_processes([3000, 3001, 3002, 3003])
    
    # 方法2: 根据进程特征清理
    try:
        subprocess.run([
            'pkill', '-f', r'python.*http\.server.*3000'
        ], capture_output=True)
        subprocess.run([
            'pkill', '-f', r'python.*-m.*http\.server'
        ], capture_output=True)
    except Exception as e:
        logger.warning(f"根据进程特征清理时出现警告: {e}")

def start_frontend_server():
    """启动前端HTTP服务器"""
    log_service_event("Frontend Server", "starting")
    
    # 首先清理可能的残留进程
    cleanup_frontend_processes()
    time.sleep(1)  # 等待端口释放
    
    # 寻找可用端口
    port = find_available_port(3000)
    if port is None:
        log_service_event("Frontend Server", "failed", "无法找到可用端口 (尝试范围: 3000-3009)", "error")
        return None, None
    
    frontend_dir = project_root / "frontend-web"
    if not frontend_dir.exists():
        log_service_event("Frontend Server", "failed", f"前端目录不存在: {frontend_dir}", "error")
        return None, None
    
    try:
        frontend_cmd = [
            sys.executable, '-m', 'http.server', str(port)
        ]
        
        frontend_process = subprocess.Popen(
            frontend_cmd,
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # 等待服务器启动
        time.sleep(2)
        
        # 检查进程是否仍在运行
        if frontend_process.poll() is None:
            # 验证端口是否真的在监听
            if not is_port_available(port):
                details = f"http://localhost:{port} (PID: {frontend_process.pid})"
                log_service_event("Frontend Server", "started", details)
                return frontend_process, port
            else:
                log_service_event("Frontend Server", "failed", "端口未被监听", "error")
                frontend_process.terminate()
                return None, None
        else:
            log_service_event("Frontend Server", "failed", "进程启动后立即退出", "error")
            return None, None
            
    except Exception as e:
        log_service_event("Frontend Server", "failed", f"启动异常: {str(e)}", "error")
        return None, None

def check_redis():
    """检查Redis服务状态"""
    logger.info("检查Redis服务状态...")
    try:
        result = subprocess.run(['redis-cli', 'ping'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and 'PONG' in result.stdout:
            logger.info("Redis服务正常运行")
            return True
        else:
            logger.error("Redis服务未响应")
            return False
    except FileNotFoundError:
        logger.error("Redis未安装，请先安装Redis: brew install redis")
        return False
    except subprocess.TimeoutExpired:
        logger.error("Redis连接超时")
        return False
    except Exception as e:
        logger.error(f"Redis检查失败: {e}")
        return False

def start_redis():
    """启动Redis服务"""
    log_service_event("Redis", "checking")
    try:
        # 检查Redis是否已经运行
        if check_redis():
            log_service_event("Redis", "already_running", "Redis服务已在运行")
            return True
        
        log_service_event("Redis", "starting", "通过brew启动Redis服务")
        # 尝试启动Redis服务
        subprocess.run(['brew', 'services', 'start', 'redis'], 
                      check=True, capture_output=True)
        
        # 等待Redis启动
        for i in range(10):
            time.sleep(1)
            if check_redis():
                log_service_event("Redis", "started", f"Redis服务启动成功 (耗时: {i+1}秒)")
                return True
            logger.info(f"等待Redis启动... ({i+1}/10)")
        
        log_service_event("Redis", "failed", "Redis启动超时", "error")
        return False
        
    except subprocess.CalledProcessError as e:
        log_service_event("Redis", "failed", f"启动命令失败: {str(e)}", "error")
        return False
    except Exception as e:
        log_service_event("Redis", "failed", f"启动异常: {str(e)}", "error")
        return False

def start_celery_worker():
    """启动Celery Worker"""
    log_service_event("Celery Worker", "starting")
    
    worker_cmd = [
        sys.executable, 'start_worker.py'
    ]
    
    try:
        # 启动Worker进程
        worker_process = subprocess.Popen(
            worker_cmd,
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # 等待Worker初始化
        logger.info("等待Celery Worker初始化...")
        time.sleep(5)
        
        # 检查进程是否仍在运行
        if worker_process.poll() is None:
            details = f"PID: {worker_process.pid}"
            log_service_event("Celery Worker", "started", details)
            return worker_process
        else:
            log_service_event("Celery Worker", "failed", "进程启动后立即退出", "error")
            return None
            
    except Exception as e:
        log_service_event("Celery Worker", "failed", f"启动异常: {str(e)}", "error")
        return None

def start_fastapi_server():
    """启动FastAPI主服务"""
    log_service_event("FastAPI Server", "starting")
    
    server_cmd = [
        sys.executable, 'run_server.py'
    ]
    
    try:
        # 启动服务器进程
        server_process = subprocess.Popen(
            server_cmd,
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # 等待服务器启动
        logger.info("等待FastAPI服务器初始化...")
        time.sleep(8)
        
        # 检查进程是否仍在运行
        if server_process.poll() is None:
            details = f"http://localhost:8000 (PID: {server_process.pid})"
            log_service_event("FastAPI Server", "started", details)
            return server_process
        else:
            log_service_event("FastAPI Server", "failed", "进程启动后立即退出", "error")
            return None
            
    except Exception as e:
        log_service_event("FastAPI Server", "failed", f"启动异常: {str(e)}", "error")
        return None

def test_system():
    """测试系统连接"""
    logger.info("开始系统连接测试...")
    
    try:
        import requests
        import json
        
        # 测试健康检查
        logger.info("测试主服务健康检查...")
        response = requests.get('http://localhost:8000/health', timeout=10)
        if response.status_code == 200:
            logger.info("主服务健康检查通过")
        else:
            logger.error(f"主服务健康检查失败: {response.status_code}")
            return False
        
        # 测试Celery连接
        logger.info("测试Celery连接...")
        response = requests.get('http://localhost:8000/tasks/health', timeout=15)
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Celery连接测试成功: {result['data']['celery_status']}")
        else:
            logger.error(f"Celery连接测试失败: {response.status_code}")
            return False
        
        # 测试系统状态
        logger.info("获取系统状态...")
        response = requests.get('http://localhost:8000/system/status', timeout=10)
        if response.status_code == 200:
            status = response.json()['data']
            logger.info("系统状态正常:")
            logger.info(f"  Celery Worker: {status['celery']['workerCount']} 个")
            logger.info(f"  WebSocket连接: {status['websocket']['activeConnections']} 个")
            logger.info(f"  推送任务: {status['pushTasks']['count']} 个")
        else:
            logger.error(f"系统状态获取失败: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"系统测试失败: {e}")
        return False

def cleanup_processes():
    """清理可能残留的进程"""
    logger.info("清理可能残留的进程...")
    
    # 清理前端服务器进程
    cleanup_frontend_processes()
    
    # 清理Celery进程
    try:
        subprocess.run(['pkill', '-f', 'celery.*worker'], 
                      capture_output=True, check=False)
        subprocess.run(['pkill', '-f', 'start_worker'], 
                      capture_output=True, check=False)
    except:
        pass
    
    # 清理FastAPI进程
    try:
        subprocess.run(['pkill', '-f', 'run_server'], 
                      capture_output=True, check=False)
        subprocess.run(['pkill', '-f', 'uvicorn'], 
                      capture_output=True, check=False)
    except:
        pass
    
    time.sleep(2)
    logger.info("进程清理完成")

def signal_handler(signum, frame):
    """信号处理函数"""
    logger.info(f"收到信号 {signum}，正在关闭服务...")
    process_manager.graceful_shutdown_all()
    cleanup_processes()
    sys.exit(0)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='InfluAI 系统启动器')
    parser.add_argument('--no-test', action='store_true', 
                       help='跳过系统连接测试')
    parser.add_argument('--cleanup', action='store_true', 
                       help='清理残留进程后退出')
    parser.add_argument('--flower', action='store_true', 
                       help='同时启动Flower监控界面')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("InfluAI 系统启动器")
    print("=" * 60)
    print()
    
    # 如果只是清理进程
    if args.cleanup:
        cleanup_processes()
        return
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 清理残留进程
    cleanup_processes()
    
    processes = []
    
    try:
        # 1. 启动Redis
        if not start_redis():
            logger.error("Redis启动失败，无法继续")
            return
        
        # 2. 启动前端服务器
        frontend_process, frontend_port = start_frontend_server()
        if frontend_process:
            process_manager.register_process(frontend_process, "Frontend Server")
        else:
            logger.warning("前端服务器启动失败，但不影响后端服务")
        
        # 3. 启动Celery Worker
        worker_process = start_celery_worker()
        if not worker_process:
            logger.error("Celery Worker启动失败，无法继续")
            return
        process_manager.register_process(worker_process, "Celery Worker")
        
        # 4. 启动FastAPI服务器
        server_process = start_fastapi_server()
        if not server_process:
            logger.error("FastAPI服务器启动失败")
            process_manager.graceful_shutdown_all()
            cleanup_processes()
            return
        process_manager.register_process(server_process, "FastAPI Server")
        
        # 5. 可选：启动Flower监控
        if args.flower:
            logger.info("启动Flower监控界面...")
            flower_process = subprocess.Popen([
                sys.executable, 'start_flower.py'
            ], cwd=project_root)
            process_manager.register_process(flower_process, "Flower Monitor")
            time.sleep(3)
        
        # 6. 系统测试
        if not args.no_test:
            if test_system():
                logger.info("所有服务启动成功！")
            else:
                logger.warning("系统测试失败，但服务可能仍在运行")
        
        # 记录系统启动完成
        if enhanced_logging_available:
            LogEvents.system_event("所有服务启动完成", "系统已就绪可以使用")
        
        # 显示服务信息
        logger.info("==================== 服务信息 ====================")
        if frontend_process and frontend_port:
            logger.info(f"前端页面: http://localhost:{frontend_port}")
            if enhanced_logging_available:
                LogEvents.service_status("Frontend Server", "ready", f"http://localhost:{frontend_port}")
        logger.info("主服务: http://localhost:8000")
        logger.info("API文档: http://localhost:8000/docs")
        logger.info("健康检查: http://localhost:8000/health")
        logger.info("系统状态: http://localhost:8000/system/status")
        if args.flower:
            logger.info("Flower监控: http://localhost:5555")
        logger.info("================================================")
        
        logger.info("管理命令:")
        logger.info("停止所有服务: Ctrl+C 或 python3 start_all.py --cleanup")
        logger.info("查看系统状态: curl http://localhost:8000/system/status")
        
        logger.info("系统已就绪，按 Ctrl+C 停止所有服务")
        
        # 保持运行并监控进程
        while True:
            time.sleep(5)
            
            # 检查进程是否仍在运行
            for proc_info in process_manager.processes:
                process = proc_info['process']
                name = proc_info['name']
                if process.poll() is not None:
                    logger.warning(f"{name} 进程已退出")
                    
    except KeyboardInterrupt:
        logger.info("收到中断信号...")
    except Exception as e:
        logger.error(f"启动过程中发生错误: {e}")
    finally:
        process_manager.graceful_shutdown_all()
        cleanup_processes()
        logger.info("程序退出")

if __name__ == '__main__':
    main()
