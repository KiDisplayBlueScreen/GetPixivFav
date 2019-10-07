from selenium import webdriver
import os
import json
import requests
from requests.cookies import RequestsCookieJar
from lxml import etree
import time
import re

# user data目录
pro_dir = r'C:\Users\NTOSKRNL\AppData\Local\Google\Chrome\User Data'


def get_cookie():
    # 添加配置
    chrome_options = webdriver.ChromeOptions()
    # 静默模式
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--start-maximized')
    # 添加user data目录
    chrome_options.add_argument('user-data-dir=' + os.path.abspath(pro_dir))
    driver = webdriver.Chrome(chrome_options=chrome_options)
    # 访问后,获取cookies
    driver.get('https://www.pixiv.net/')
    cookies = driver.get_cookies()
    # 保存cookies
    with open("pixiv_cookies.txt", "w") as fp:
        json.dump(cookies, fp)
    driver.close()


def read_cookie():
    jar = RequestsCookieJar()
    with open("pixiv_cookies.txt", "r") as fp:
        cookies = json.load(fp)
        for cookie in cookies:
            jar.set(cookie['name'], cookie['value'])
    return jar


def rep(jar, PageNum):
    Suffix = '?rest=show&p=' + str(PageNum)
    url = 'https://www.pixiv.net/bookmark.php' + Suffix
    headers = {
        'referer': 'https://accounts.pixiv.net/login',
        'origin': 'https://accounts.pixiv.net',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}
    html = se.get(url, headers=headers, cookies=jar)
    if html.status_code != 200:
        return 0
    return html


def GetFavImageURL():
    ImageURL = 'https://www.pixiv.net/artworks/'
    Parser = etree.HTMLParser(encoding="utf-8")
    Html = etree.parse(r'D:\Python32\FavImage.html', parser=Parser)
    # Html_Data = etree.tostring(Html, encoding="utf-8")
    # Result = Html_Data.decode('utf-8')

    XPath_GetImageURL = '//li[@class="image-item"]/a[1]/@href'
    Fav_Image_URL = Html.xpath(XPath_GetImageURL)
    Fav_Image_URL_List = []
    print('\n')
    j = 1
    for i in Fav_Image_URL:
        # print("No." + str(j) + " " + i)
        Fav_Image_URL_List.append(ImageURL + Fav_Image_URL[j - 1][40:])
        j = j + 1
    return Fav_Image_URL_List


def GetFavImagePage(FavImageURL, jar):
    Headers = \
        {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36'
        }
    try:
        Html = se.get(FavImageURL, headers=Headers, cookies=jar)
    except:
        print('Get Fav Error')
        print(requests.exceptions)
        return 0
    else:
        return Html


def WriteFavImageFile(FavImageHtml_Text, Order):
    IsExist = os.path.exists(r'D:\PythonCode\Gallery Html Page')
    if not IsExist:
        os.mkdir(r"D:\PythonCode\Gallery Html Page")
    FileHandle = open(r"D:\PythonCode\Gallery Html Page\\" + str(Order) + ".html", 'w+', encoding='utf-8')
    FileHandle.write(FavImageHtml_Text)
    FileHandle.close()
    return 1


def GetTempURL(HtmlPath):  # 参数为保存在本机的Html页面
    Parser = etree.HTMLParser(encoding="utf-8")
    Html = etree.parse(HtmlPath, parser=Parser)
    Html_Data = etree.tostring(Html, encoding="utf-8")
    Result = Html_Data.decode('utf-8')
    ReExpression = '\"original\"'
    ResultTuple = re.search(ReExpression, Result).span()  # 返回符合要求的子串的起始位置与结束位置
    StartPos = ResultTuple[0] + 12
    EndPos = ResultTuple[1] + 85
    TempURL = Result[StartPos:EndPos]
    return TempURL


def FullImageURLGen(TempImageURL):
    ImageURLPre = 'https://i.pximg.net/img-original/img/'
    ImageURLSuffix = '.png'
    ImageURLMain = TempImageURL[42:46] + '/' + TempImageURL[48:50] + '/' + TempImageURL[52:54] + '/' + TempImageURL[
                                                                                                       56:58] + '/' + TempImageURL[
                                                                                                                      60:62] + '/' + TempImageURL[
                                                                                                                                     64:66] + '/' + TempImageURL[
                                                                                                                                                    68:79]
    FullImageURL = ImageURLPre + ImageURLMain + ImageURLSuffix
    return FullImageURL


def GetPixivID(ImageURL):
    return ImageURL[57:65]


def GetImage(ImageURL, jar, PixivID):
    headers = \
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.86 Safari/537.36",
            'Host': 'i.pximg.net',
            'Accept': '*.*'
        }
    Ref = ImageURL[0:57]  # 必须加上Referer字段否则报404
    headers["Referer"] = Ref
    try:
        Image = se.get(ImageURL, cookies=jar, headers=headers)
    except:
        print('Get Fav Error')
        print(requests.exceptions)
        return 0
    else:
        if Image.status_code == 200:
            print("Get Image Success." + '\n')
        if Image.status_code == 404:
            print("Get Image Fail,Try to Change The URL...")
            ImageURL = ImageURL[0:57] + PixivID + '_p0.jpg'
            Image = se.get(ImageURL, cookies=jar, headers=headers)
            if Image.status_code == 200:
                print("Get Image Success." + '\n')

        IsExist = os.path.exists(r'D:\Image')
        if not IsExist:
            os.mkdir(r"D:\Image")
        FileHandle = open(r"D:\Image\\" + PixivID + ".png", 'wb+')
        FileHandle.write(Image.content)
        FileHandle.close()
        GetMultiImage(ImageURL, jar, PixivID, headers)
        return 1


def GetMultiImage(ImageURL, jar, PixivID, headers):
    i = 1
    while 1:
        if i > 10:
            ImageURL = ImageURL[0:67] + str(i) + ImageURL[69:]
        else:
            ImageURL = ImageURL[0:67] + str(i) + ImageURL[68:]
        print("Try Multi Image URL: " + ImageURL)
        try:
            Image = se.get(ImageURL, cookies=jar, headers=headers)
        except:
            print('Get Multi Image Error')
            print(requests.exceptions)
            return 0
        else:
            if Image.status_code != 200:
                print("This Page Does't have more than 1 Image or All of the Image have been Downloaded." + '\n')
                return 0
            print("Get Multi Image Success")
            FileHandle = open(r"D:\Image\\" + PixivID + '_p' + str(i) + ".png", 'wb+')
            FileHandle.write(Image.content)
            FileHandle.close()
            i = i + 1


if __name__ == '__main__':
    #get_cookie()  # 模拟本机浏览器行为获取Cookies
    se = requests.session()  # 定义session对象
    jar = read_cookie()  # 读取Cookies
    PageNum = input("请输入你要下载哪一页:")
    html = rep(jar, int(PageNum))  # 获取收藏页面
    if html == 0:
        get_cookie()
        jar = read_cookie()
        html = rep(jar, int(PageNum))

    with open('FavImage.html', 'w+', encoding='utf8') as fp:
        fp.write(html.text)  # 保存收藏页面为文件
    # os.system('start FavImage.html')  # 打开文件
    os.system('cls')
    Fav_Image_URL_List = GetFavImageURL()  # 创建一个列表里面存放所有的收藏URL
    j = 1
    for i in Fav_Image_URL_List:
        print('No.' + str(j) + ' FavImage: ' + i + '\n')
        FavImageHtml = GetFavImagePage(Fav_Image_URL_List[j - 1], jar)  # 依次获取所有收藏图片的页面
        WriteFavImageFile(FavImageHtml.text, j)  # 保存到本地
        j = j + 1
        time.sleep(3)

os.remove('FavImage.html')
Path = os.listdir(r'D:\PythonCode\Gallery Html Page')
j = 1
for i in Path:
    PagePath = r'D:\PythonCode\Gallery Html Page\\' + str(i)
    TempURL = GetTempURL(PagePath)  # 获取临时路径
    ImageURL = FullImageURLGen(TempURL)  # 从临时路径中获取真正的图片URL
    print("No." + str(j) + " Image: " + ImageURL)  # 将临时路径转为真正路径
    PixivID = GetPixivID(ImageURL)  # 获取PixivID
    GetImage(ImageURL, jar, PixivID)
    # print("No." + str(j) + " Image: " + ImageURL + '\n')
    j = j + 1

for i in Path:
    os.remove(r'D:\PythonCode\Gallery Html Page\\' + str(i))
