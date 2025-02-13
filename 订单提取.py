import requests, time, os
from datetime import datetime

token = ""

payStates = {
    0: "待付款",
    1: "支付中",
    2: "已付款",
    3: "支付失败",
    4: "支付超时",
    5: "5",
    6: "订单取消",
}
subsidyTypes = {
    0: "国补",
    1: "省补",
}
headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 15; 2211133C Build/AQ3A.240812.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.103 Mobile Safari/537.36 XWEB/1300289 MMWEBSDK/20241103 MMWEBID/7556 MicroMessenger/8.0.55.2780(0x2800373D) WeChat/arm64 Weixin NetType/5G Language/zh_CN ABI/arm64 MiniProgramEnv/android",
    "token": token,
    "content-type": "application/json",
    "charset": "utf-8",
    "Referer": "https://servicewechat.com/wxda2d69d2412af960/226/page-frame.html",
}


# 获取订单详情
def getSalesOrderDetail(orderNumber):
    url = "https://jsyxfw.ccb.com/sxxf/ccb_equity_api_new/salesuser/getSalesOrderDetail"
    params = {"orderNumber": orderNumber}
    return requests.get(url, params=params, headers=headers)


# 从token.txt获取token
def getTokenFromTxt():
    with open("token.txt", "r") as f:
        return f.read()


# 构造headers添加token
def generateHeaders():
    global headers
    headers["token"] = getTokenFromTxt()


# 验证token
def verifyToken():
    if not getTokenFromTxt():
        print("请先填写token")
    url = "https://jsyxfw.ccb.com/sxxf/ccb_equity_api_new/salesuser/getSalesActivity"
    res = requests.get(url, headers=headers).json()
    if res["code"] == 1001:
        print("Token失效")
        return False
    else:
        print(
            f"{res['data']['activity']['subsidyTotalAmountDisp']} 国家补贴已使用 {res['data']['activity']['usedAmountPercent']} %"
        )
        return True


# 判断日期是否为今日
def isToday(date_str):
    given_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    current_date = datetime.now()
    return given_date.date() == current_date.date()


# 获取指定页数订单列表
def getSalesPayAndRefundOrderList(pageNumber=1):
    url = "https://jsyxfw.ccb.com/sxxf/ccb_equity_api_new/salesuser/getSalesPayAndRefundOrderList"
    params = {"buyerMobile": "", "pageNumber": pageNumber, "uploadFile3COrder": ""}
    return requests.get(url, params=params, headers=headers)


# 获取今日订单
def getTodaySales():
    shopOrders = getSalesPayAndRefundOrderList().json()["data"]["shopOrders"]
    newShopOrders = [order for order in shopOrders if isToday(order["createTime"])]
    print(f"共提取 {len(shopOrders)} 条今日的订单")
    return newShopOrders


# 获取全部订单
def getAllSales():
    shopOrders = []
    isNull = False
    page = 1
    while not isNull:
        shopOrdersPage = getSalesPayAndRefundOrderList(page).json()["data"][
            "shopOrders"
        ]
        if shopOrdersPage:
            for order in shopOrdersPage:
                if order["payState"] == 2:
                    shopOrders.append(order)
            page += 1
        else:
            isNull = True
    print(f"共提取 {len(shopOrders)} 条已付款订单")

    return shopOrders


# 输出结果到txt
def writeToTex(shopOrders, isSaveAs=0):
    currentTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fileName = "订单提取.txt"
    if isSaveAs:
        fileName = "订单提取_" + datetime.now().strftime("%Y-%m-%d-%H%M") + ".txt"
    with open(fileName, "w", encoding="utf-8") as f:
        f.write("更新时间：" + currentTime)
        for order in shopOrders:
            orderNumber = order["ccbPayOrderNumber"]
            detail = getSalesOrderDetail(orderNumber).json()["data"]["payOrder"]
            good = detail["goodsOrderList"][0]
            payState = detail["payState"]
            subsidyType = good["subsidyType"]
            f.write("\n\n支付状态：" + payStates[payState])
            f.write("\n支付单号：" + orderNumber)
            f.write("\n销售单号：" + detail["shopOrderNumber"])
            f.write("\n顾客姓名：" + str(detail["buyerName"]))
            f.write("\n手机号码：" + detail["buyerMobile"])
            f.write("\n送货地区：" + detail["address"].split(" ")[0])
            f.write("\n详细地址：" + "".join(detail["address"].split(" ")[1:]))

            f.write("\n下单时间：" + str(detail["createTime"]))
            if payState == 2:
                f.write("\n支付时间：" + str(detail["payTime"]))

            f.write("\n商品编号：" + good["goodsCode"])
            f.write("\n商品名称：" + good["goodsName"])
            f.write(
                "\n补贴类型："
                + subsidyTypes[subsidyType]
                + "\t补贴单价："
                + str(int(detail["subsidyTotalAmount"]))
            )

            f.write(
                "\n门店单价："
                + str(int(detail["shopOriginalPrice"]))
                + "\t实付单价："
                + str(int(detail["shopActualPayPrice"]))
            )
    print("\n运行完成！")


def writeToCsv(shopOrders):
    fileName = "订单提取_" + datetime.now().strftime("%Y-%m-%d-%H%M") + ".csv"
    with open(fileName, "w", encoding="utf-8") as f:
        f.write(
            "支付状态,支付单号,销售单号,顾客姓名,手机号码,送货地区,详细地址,下单时间,支付时间,商品编号,商品名称,补贴类型,补贴单价,门店单价,实付单价\n"
        )
        for order in shopOrders:
            orderNumber = order["ccbPayOrderNumber"]
            detail = getSalesOrderDetail(orderNumber).json()["data"]["payOrder"]
            good = detail["goodsOrderList"][0]
            payState = detail["payState"]
            subsidyType = good["subsidyType"]
            lineData = [
                payStates[payState],
                orderNumber,
                detail["shopOrderNumber"],
                str(detail["buyerName"]),
                detail["buyerMobile"],
                detail["address"].split(" ")[0],
                "".join(detail["address"].split(" ")[1:]),
                str(detail["createTime"]),
                str(detail["payTime"]) if payState == 2 else "",
                good["goodsCode"],
                good["goodsName"],
                subsidyTypes[subsidyType],
                str(int(detail["subsidyTotalAmount"])),
                str(int(detail["shopOriginalPrice"])),
                str(int(detail["shopActualPayPrice"])),
            ]
            f.write(",".join(lineData))
            f.write("\n")
    print("\n运行完成！")


if __name__ == "__main__":
    os.system("cls")

    generateHeaders()

    if not verifyToken():
        exit()

    writeToTex(getAllSales())

    needSaveAs = input("是否另存为？\n(默认跳过)\n1 另存为txt\n2 另存为csv\n")
    if needSaveAs == "1":
        writeToTex(getAllSales(), 1)
    elif needSaveAs == "2":
        writeToCsv(getAllSales())
