import requests
import logging
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import threading
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API 配置
DATA_API_URL = "https://s00reg.64t76dee9sk5.workers.dev/api"
NOTIFICATION_API_URL = "https://api.day.app/Y6wZN8swvDrno2URYa5CDZ/"

# 创建数据队列和计数器
user_data_queue = Queue()
MAX_WORKERS = 10  # 并发线程数

# 添加计数器类
class RegistrationCounter:
    def __init__(self):
        self.total_attempts = 0
        self.successful_registrations = 0
        self.failed_registrations = 0
        self._lock = threading.Lock()
        self.start_time = datetime.now()

    def increment_attempt(self):
        with self._lock:
            self.total_attempts += 1

    def increment_success(self):
        with self._lock:
            self.successful_registrations += 1

    def increment_failure(self):
        with self._lock:
            self.failed_registrations += 1

    def get_stats(self):
        duration = datetime.now() - self.start_time
        hours = duration.total_seconds() / 3600
        success_rate = (self.successful_registrations / self.total_attempts * 100) if self.total_attempts > 0 else 0
        registrations_per_hour = self.successful_registrations / hours if hours > 0 else 0

        return {
            "总尝试次数": self.total_attempts,
            "成功注册数": self.successful_registrations,
            "失败次数": self.failed_registrations,
            "运行时间": str(duration).split('.')[0],
            "成功率": f"{success_rate:.2f}%",
            "每小时注册数": f"{registrations_per_hour:.2f}"
        }

# 创建全局计数器实例
counter = RegistrationCounter()

# 高级伪装设置
def advanced_stealth(driver):
    """注入高级伪装脚本，隐藏 Selenium 痕迹"""
    stealth_script = """
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
    Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
    Object.defineProperty(Intl.DateTimeFormat.prototype, 'resolvedOptions', {
        value: () => ({ timeZone: 'America/New_York' })
    });
    Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
    Object.defineProperty(navigator, 'deviceMemory', { get: () => 16 });
    Object.defineProperty(navigator, 'maxTouchPoints', { get: () => 2 });
    const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        if (parameter === 37445) return 'NVIDIA Corporation';
        if (parameter === 37446) return 'NVIDIA GeForce GTX 1080';
        return originalGetParameter.call(this, parameter);
    };
    """
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": stealth_script})
    logging.info("高级伪装已启用")

# 初始化 WebDriver
def init_webdriver(user_agent):
    """初始化浏览器，并设置伪装参数"""
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--incognito")
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(options=options)
    advanced_stealth(driver)
    logging.info("WebDriver 初始化完成")
    return driver

# 获取用户数据
def fetch_user_data():
    """获取用户数据，若失败则重试"""
    while True:
        try:
            response = requests.get(DATA_API_URL)
            response.raise_for_status()
            data = response.json()
            return data['url'], data['user'], data['userAgent']
        except Exception as e:
            logging.error(f"获取用户数据失败，重试中: {e}")
            time.sleep(2)

# 数据预加载线程
def data_preloader():
    """持续预加载用户数据到队列"""
    while True:
        try:
            if user_data_queue.qsize() < MAX_WORKERS * 2:
                data = fetch_user_data()
                user_data_queue.put(data)
                logging.info(f"预加载数据成功，当前队列大小: {user_data_queue.qsize()}")
        except Exception as e:
            logging.error(f"预加载数据失败: {e}")
        time.sleep(1)

# 填写表单
def fill_form(driver, user):
    """填写注册表单"""
    wait = WebDriverWait(driver, 10)
    try:
        wait.until(EC.presence_of_element_located((By.ID, "id_first_name"))).send_keys(user['firstName'])
        wait.until(EC.presence_of_element_located((By.ID, "id_last_name"))).send_keys(user['lastName'])
        wait.until(EC.presence_of_element_located((By.ID, "id_username"))).send_keys(user['username'])
        wait.until(EC.presence_of_element_located((By.ID, "id_email"))).send_keys(user['email'])
        wait.until(EC.presence_of_element_located((By.ID, "id_question"))).send_keys("1000")
        
        tos_checkbox = wait.until(EC.element_to_be_clickable((By.ID, "id_tos")))
        if not tos_checkbox.is_selected():
            tos_checkbox.click()
        logging.info(f"表单填写完成: {user}")
    except Exception as e:
        logging.error(f"表单填写失败: {e}")
        return False
    return True

# 解决验证码
def solve_captcha(image_path):
    """调用OCR API解决验证码"""
    api_url = "https://ocrapi.gits.one/?ocr"
    headers = {'Authorization': 'Bearer fivl7VyjCAYWmUgWj1psGfxz71aqFHmOFSsdWdyEjipSWiQZUXzc0E039PQszBzu'}
    while True:
        try:
            with open(image_path, 'rb') as image_file:
                response = requests.post(api_url, headers=headers, files={'image': image_file})
                response.raise_for_status()
                result = response.json()
                if result['success']:
                    captcha_code = result['result']
                    logging.info(f"验证码识别成功: {captcha_code}")
                    return captcha_code
                else:
                    logging.warning("验证码识别失败，重试中")
        except Exception as e:
            logging.error(f"OCR API 调用失败: {e}")
        time.sleep(2)

# 等待注册结果并处理验证码
def wait_for_result(driver, attempt_number):
    """等待注册结果，并处理验证码"""
    counter.increment_attempt()
    start_time = time.time()
    captcha_filled = False

    while time.time() - start_time < 60:
        try:
            success_notification = driver.find_element(By.CSS_SELECTOR, ".notification.is-success")
            if success_notification.is_displayed():
                counter.increment_success()
                logging.info(f"注册成功 (尝试次数: {attempt_number})")
                logging.info(success_notification.text)
                return True
        except:
            pass

        try:
            error_message = driver.find_element(By.CSS_SELECTOR, ".error_message")
            if error_message.is_displayed():
                counter.increment_failure()
                logging.error(f"注册失败: {error_message.text}\n\n")
                return False
        except:
            pass

        try:
            captcha_image = driver.find_element(By.CSS_SELECTOR, ".captcha")
            if not captcha_filled and captcha_image.is_displayed():
                captcha_image_path = f"/tmp/captcha_image_{threading.get_ident()}.png"
                with open(captcha_image_path, 'wb') as file:
                    file.write(captcha_image.screenshot_as_png)
                captcha_code = solve_captcha(captcha_image_path)
                if captcha_code:
                    driver.find_element(By.ID, "id_captcha_1").send_keys(captcha_code)
                    driver.find_element(By.CSS_SELECTOR, ".button.is-primary").click()
                    captcha_filled = True
        except:
            pass

        time.sleep(0.5)

    counter.increment_failure()
    logging.warning(f"注册超时 (尝试次数: {attempt_number})")
    return False

# 发送注册成功通知
def send_success_notification(user, user_agent):
    """发送注册信息保存请求到指定接口"""
    try:
        data = {
            "username": user['username'],
            "email": user['email'],
            "name": f"{user['firstName']} {user['lastName']}",
            "ua": user_agent
        }

        response = requests.post(
            "https://keamlv.serv00.net/create_account.php",
            headers={"Content-Type": "application/json"},
            data=json.dumps(data)
        )
        
        response.raise_for_status()
        response_data = response.json()
        
        if response_data.get("status") == "success":
            logging.info(f"注册信息保存成功: {response_data}")
        else:
            logging.error(f"注册信息保存失败: {response_data.get('message', '未知错误')}")
    
    except Exception as e:
        logging.error(f"保存注册信息失败: {e}")

# 单个注册线程的处理函数
def registration_worker():
    """单个注册工作线程的处理逻辑"""
    driver = None
    attempt_number = 0
    
    try:
        while True:
            attempt_number += 1
            if driver is None:
                # 从队列获取数据
                registration_url, user, user_agent = user_data_queue.get()
                driver = init_webdriver(user_agent)
            
            try:
                logging.info(f"线程 {threading.get_ident()} 开始第 {attempt_number} 次注册")
                
                driver.get(registration_url)
                if fill_form(driver, user):
                    if wait_for_result(driver, attempt_number):
                        send_success_notification(user, user_agent)
                
                # 获取新的注册数据
                registration_url, user, user_agent = user_data_queue.get()
                
            except Exception as e:
                logging.error(f"注册过程发生错误: {e}")
                if driver:
                    driver.quit()
                    driver = None
    finally:
        if driver:
            driver.quit()

# 状态打印函数
def print_stats():
    """定期打印注册统计信息"""
    while True:
        stats = counter.get_stats()
        logging.info("\n=== 注册统计信息 ===")
        for key, value in stats.items():
            logging.info(f"{key}: {value}")
        logging.info("==================\n")
        time.sleep(60)  # 每60秒打印一次统计信息

# 主函数
def main():
    """主程序入口"""
    # 启动数据预加载线程
    preloader = threading.Thread(target=data_preloader, daemon=True)
    preloader.start()
    
    # 启动统计信息打印线程
    stats_printer = threading.Thread(target=print_stats, daemon=True)
    stats_printer.start()
    
    # 等待预加载队列中有足够的数据
    while user_data_queue.qsize() < MAX_WORKERS:
        time.sleep(1)
    
    try:
        # 创建线程池并启动工作线程
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            workers = [executor.submit(registration_worker) for _ in range(MAX_WORKERS)]
            
            # 等待所有工作线程完成
            for future in workers:
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"工作线程异常退出: {e}")
    except KeyboardInterrupt:
        logging.info("检测到键盘中断，正在优雅退出...")
    finally:
        # 程序结束时打印最终统计信息
        final_stats = counter.get_stats()
        logging.info("\n=== 最终注册统计信息 ===")
        for key, value in final_stats.items():
            logging.info(f"{key}: {value}")
        logging.info("=====================\n")

if __name__ == "__main__":
    main()
