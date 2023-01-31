from pathlib import Path
import urllib.request
from selenium import webdriver
from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

ACCEPTABLE_EXT = ["jpg", "jpeg", "png", "webp"]
CHROMEDRIVER_PATH = "/usr/lib/chromium-browser/chromedriver"


def crawl_google_image(
    query: str,
    limit: int = 10,
    download_dir: str = "/data/imdb-actor-image",
):
    large_limit = int(limit * 1.5)

    download_dir = Path(download_dir) / query
    download_dir.mkdir(parents=True, exist_ok=True)

    count = {
        "success": len(list(download_dir.glob("*.*"))),
        "fail": 0,
    }

    if count["success"] >= limit:
        return

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"
    )
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options,
    )

    driver.get("https://www.google.co.kr/imghp?hl=en")
    elem = driver.find_element(By.NAME, "q")
    elem.send_keys(query)
    elem.send_keys(Keys.RETURN)

    sleep(2)

    last_height = driver.execute_script("return document.body.scrollHeight")

    img_element_list = list()
    while len(img_element_list) < large_limit:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        sleep(1)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            try:
                # 결과 더보기
                driver.find_element(".mye4qd").click()
            except:
                break
        last_height = new_height

        img_element_list = list(
            driver.find_elements(By.CSS_SELECTOR, "img.rg_i.Q4LuWd")
        )

    image_src_list = list()
    for img in img_element_list[count["success"] + 1 : large_limit]:
        try:
            img.click()
        except:
            count["fail"] += 1
            continue

        sleep(0.5)

        image_src_list.append(
            driver.find_element(
                By.XPATH,
                '//*[@id="Sva75c"]/div[2]/div/div[2]/div[2]/div[2]/c-wiz/div[2]/div[1]/div[1]/div[2]/div/a/img',
            ).get_attribute("src")
        )

    for link in image_src_list:
        try:
            link = link.split("?")[0]
            ext = link.split(".")[-1]
            if ext.lower() in ACCEPTABLE_EXT:
                image_path = download_dir / f"{count['success']}.{ext}"
                image_path = str(image_path.absolute())
                urllib.request.urlretrieve(link, image_path)
                count["success"] += 1
        except Exception as e:
            print(f"ERROR [{query}] {count['fail']:03d} - {link}")
            print(e)


if __name__ == "__main__":
    crawl_google_image(
        query="Hugh Jackman",
        limit=10,
        download_dir="/data/imdb-actor-image",
    )
