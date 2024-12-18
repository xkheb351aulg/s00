import requests
import logging
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from threading import Thread

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API 配置
DATA_API_URL = "https://s00reg.64t76dee9sk5.workers.dev/666"
NOTIFICATION_API_URL = "https://api.day.app/Y6wZN8swvDrno2URYa5CDZ/"
REGISTRATION_URL = "https://www.serv00.com/offer/create_new_account"

# 初始化 WebDriver 配置（更高级的伪装）
def init_webdriver(user_agent):
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--incognito")
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(options=options)

    # 注入高级伪装脚本
    script = """
    // 隐藏 WebDriver 属性
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

    // 伪造插件信息
    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });

    // 伪造语言和时区
    Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
    Object.defineProperty(Intl.DateTimeFormat.prototype, 'resolvedOptions', {
        value: () => ({ timeZone: 'America/New_York' })
    });

    // 伪造硬件信息
    Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 4 });
    Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
    Object.defineProperty(screen, 'width', { get: () => 1920 });
    Object.defineProperty(screen, 'height', { get: () => 1080 });

    // 禁用 WebRTC
    Object.defineProperty(navigator, 'mediaDevices', { 
        get: () => ({ getUserMedia: () => { throw new Error("WebRTC is disabled"); } }) 
    });

    // 禁用 WebGL 指纹检测
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        // 避免暴露 GPU 供应商和渲染器信息
        if (parameter === 37445 || parameter === 37446) {
            return "Intel Open Source Technology Center";
        }
        return getParameter(parameter);
    };

    // 模拟真实插件
    Object.defineProperty(navigator, 'mimeTypes', { 
        get: () => [{ type: 'application/pdf' }, { type: 'application/x-google-chrome-pdf' }] 
    });
    """
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": script})
    logging.info("WebDriver 已完成高级伪装")
    return driver

# 获取用户数据
def fetch_user_data():
    while True:
        try:
            response = requests.get(DATA_API_URL)
            response.raise_for_status()
            data = response.json()
            return data['user'], data['userAgent']
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
        logging.info(f"{user['firstName']} {user['lastName']} 填写表单完成")
    except Exception as e:
        logging.error(f"填写表单失败: {e}")
        return False
    return True

# 等待注册结果并处理验证码
def wait_for_result(driver, attempt_number):
    start_time = time.time()
    while time.time() - start_time < 60:
        try:
            success_notification = driver.find_element(By.CSS_SELECTOR, ".notification.is-success")
            if success_notification.is_displayed():
                logging.info(f"第 {attempt_number} 次注册成功！")
                return True
        except:
            pass

        try:
            error_message = driver.find_element(By.CSS_SELECTOR, ".error_message")
            if error_message.is_displayed():
                logging.error(f"注册失败: {error_message.text}")
                return False
        except:
            pass

        time.sleep(0.5)

    logging.warning(f"第 {attempt_number} 次注册超时，未检测到成功或失败的提示")
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

    preload_thread = Thread(target=preload_user_data, args=(preloaded_data,))
    preload_thread.start()

    driver = None
    try:
        while True:
            attempt_number += 1
            logging.info(f"开始第 {attempt_number} 次注册 Serv00")

            try:
                if preloaded_data['data']:
                    user, user_agent = preloaded_data['data']
                    preload_thread = Thread(target=preload_user_data, args=(preloaded_data,))
                    preload_thread.start()
                else:
                    user, user_agent = fetch_user_data()

                if not driver:
                    driver = init_webdriver(user_agent)

                driver.get(REGISTRATION_URL)
                fill_form(driver, user)

                if wait_for_result(driver, attempt_number):
                    send_success_notification(user['username'])

            except Exception as e:
                logging.error(f"第 {attempt_number} 次注册发生错误: {e}，重新尝试...")

    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
