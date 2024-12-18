import requests
import logging
import time
from threading import Thread
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API 配置
DATA_API_URL = "https://s00reg.64t76dee9sk5.workers.dev/666"
NOTIFICATION_API_URL = "https://api.day.app/Y6wZN8swvDrno2URYa5CDZ/"

# 固定注册 URL
REGISTRATION_URL = "https://www.serv00.com/offer/create_new_account"

# 初始化 WebDriver 配置
def init_webdriver(user_agent, proxy=None):
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--incognito")
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")

    # 模拟语言设置
    options.add_argument("--lang=en-US")

    # 模拟屏幕分辨率
    options.add_argument("--window-size=1920,1080")

    # 添加代理
    if proxy:
        options.add_argument(f"--proxy-server={proxy}")

    # 隐藏 Selenium 特征
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # 配置性能
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=options)

    # 进一步隐藏特征
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
            Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 4});
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ? Promise.resolve({ state: 'denied' }) : originalQuery(parameters)
            );
        """
    })

    return driver

# 获取用户数据
def fetch_user_data():
    while True:
        try:
            response = requests.get(DATA_API_URL)
            response.raise_for_status()
            data = response.json()
            return data['user'], data['userAgent'], data.get('proxy')
        except Exception as e:
            logging.error(f"获取用户数据失败，重试中: {e}")
            time.sleep(2)

# 预加载下一次注册数据
def preload_user_data(preloaded_data):
    try:
        preloaded_data['data'] = fetch_user_data()
    except Exception as e:
        logging.error(f"预加载用户数据失败: {e}")

# 填写表单
def fill_form(driver, user):
    wait = WebDriverWait(driver, 10)
    try:
        wait.until(EC.presence_of_element_located((By.ID, "id_first_name"))).send_keys(user['firstName'])
        wait.until(EC.presence_of_element_located((By.ID, "id_last_name"))).send_keys(user['lastName'])
        wait.until(EC.presence_of_element_located((By.ID, "id_username"))).send_keys(user['username'])
        wait.until(EC.presence_of_element_located((By.ID, "id_email"))).send_keys(user['email'])
        wait.until(EC.presence_of_element_located((By.ID, "id_question"))).send_keys("1000")

        # 勾选服务条款
        tos_checkbox = wait.until(EC.element_to_be_clickable((By.ID, "id_tos")))
        if not tos_checkbox.is_selected():
            tos_checkbox.click()

        logging.info(f"填写表单成功: {user['username']}, {user['email']}")
    except Exception as e:
        logging.error(f"填写表单失败: {e}")
        return False
    return True

# 等待注册结果
def wait_for_result(driver, attempt_number):
    start_time = time.time()
    while time.time() - start_time < 60:
        try:
            # 检查是否有注册成功的通知
            success_notification = driver.find_element(By.CSS_SELECTOR, ".notification.is-success")
            if success_notification.is_displayed():
                logging.info(f"第 {attempt_number} 次注册成功！")
                return True
        except:
            pass

        try:
            # 检查是否有注册失败的错误信息
            error_message = driver.find_element(By.CSS_SELECTOR, ".error_message")
            if error_message.is_displayed():
                logging.error(f"注册失败: {error_message.text}")
                return False
        except:
            pass

    logging.warning(f"第 {attempt_number} 次注册超时")
    return False

# 发送注册成功通知
def send_success_notification(username):
    try:
        response = requests.get(f"{NOTIFICATION_API_URL}{username}@proton.me")
        response.raise_for_status()
        logging.info(f"注册成功通知发送完成: {username}@proton.me")
    except Exception as e:
        logging.error(f"发送注册成功通知失败: {e}")

# 主流程
def main():
    preloaded_data = {'data': None}
    attempt_number = 0

    # 异步预加载下一次数据
    preload_thread = Thread(target=preload_user_data, args=(preloaded_data,))
    preload_thread.start()

    driver = None
    try:
        while True:
            attempt_number += 1
            logging.info(f"开始第 {attempt_number} 次注册 Serv00")

            try:
                # 如果预加载数据已完成，使用预加载数据；否则直接获取
                if preloaded_data['data']:
                    user, user_agent, proxy = preloaded_data['data']
                    preload_thread = Thread(target=preload_user_data, args=(preloaded_data,))
                    preload_thread.start()
                else:
                    user, user_agent, proxy = fetch_user_data()

                # 初始化 WebDriver（只在第一次初始化）
                if not driver:
                    driver = init_webdriver(user_agent, proxy)

                # 访问注册页面
                driver.get(REGISTRATION_URL)

                # 填写表单
                if fill_form(driver, user):
                    # 验证注册结果
                    if wait_for_result(driver, attempt_number):
                        logging.info(f"注册成功！邮箱: {user['email']}")
                        send_success_notification(user['username'])

            except Exception as e:
                logging.error(f"第 {attempt_number} 次注册发生错误: {e}")

    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
