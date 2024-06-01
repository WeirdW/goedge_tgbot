import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests
import json  # Ensure to import json

# 配置日志记录
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levellevel)s - %(message)s',
    level=logging.INFO
)

API_TOKEN = "7327775247:AAGB1JRnCqCVX4PYTXMYTiGx54sz-CCO-yo"

# 在这里定义全局变量来存储用户的goedge cdn api信息
user_edge_info = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        '欢迎使用 Goedge Cdn 看板查询机器人！请发送你的API节点的HTTP访问地址，用户类型(user/admin)，AccessKey ID，AccessKey密钥，格式如下：\n'
        '/config <API节点HTTP访问地址> <用户类型> <AccessKey ID> <AccessKey密钥>'
    )

async def config(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 4:
        await update.message.reply_text('格式错误！请发送 /config <API节点HTTP访问地址> <用户类型> <AccessKey ID> <AccessKey密钥>')
        return
    
    api_url, user_type, accessKeyId, accessKey = context.args  # Renamed 'type' to 'user_type'
    user_id = update.message.from_user.id
    user_edge_info[user_id] = {'api_url': api_url, 'type': user_type, 'accessKeyId': accessKeyId, 'accessKey': accessKey}
    await update.message.reply_text('配置成功！请使用 /token 获取AccessToken。')

async def get_AccessToken(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id not in user_edge_info:
        await update.message.reply_text('请先使用 /config 命令配置你的API节点。')
        return

    api_url = user_edge_info[user_id]['api_url']
    user_type = user_edge_info[user_id]['type']
    accessKeyId = user_edge_info[user_id]['accessKeyId']
    accessKey = user_edge_info[user_id]['accessKey']
    
    data = {
        "type": user_type,
        "accessKeyId": accessKeyId,
        "accessKey": accessKey
    }
    json_data = json.dumps(data)
    headers = {'Content-Type': 'application/json'}
    response = requests.post(f"{api_url}/APIAccessTokenService/getAPIAccessToken", data=json_data, headers=headers)
    
    # 打印调试信息
    logging.info(f'API响应状态码: {response.status_code}')
    logging.info(f'API响应内容: {response.text}')

    if response.status_code == 200:
        try:
            data = response.json()
            logging.info(f'解析后的响应数据: {data}')
            token = data.get('data', {}).get('token')
            if not token:
                await update.message.reply_text('未获取到token。')
                return

            # Store the token for further requests
            user_edge_info[user_id]['token'] = token

            message = f"AccessToken：\n {token}"
            await update.message.reply_text(message)
        except ValueError:
            await update.message.reply_text('解析响应失败，返回的不是有效的JSON格式。')
    else:
        await update.message.reply_text(f'获取token失败，状态码：{response.status_code}，响应内容：{response.text}')

async def get_ServerStatBoard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id not in user_edge_info or 'token' not in user_edge_info[user_id]:
        await update.message.reply_text('请先使用 /config 和 /token 命令配置你的API节点并获取token。')
        return

    if len(context.args) != 1:
        await update.message.reply_text('格式错误！请发送 /composeServerStatBoard <服务ID>')
        return

    server_id = context.args[0]
    api_url = user_edge_info[user_id]['api_url']
    token = user_edge_info[user_id]['token']
    
    headers = {
        'Content-Type': 'application/json',
        'X-Edge-Access-Token': token
    }
    data = {
        "serverId": int(server_id)
    }
    json_data = json.dumps(data)
    response = requests.post(f"{api_url}/ServerStatBoardService/composeServerStatBoard", data=json_data, headers=headers)
    
    # 打印调试信息
    logging.info(f'API响应状态码: {response.status_code}')
    logging.info(f'API响应内容: {response.text}')

    if response.status_code == 200:
        try:
            data = response.json()
            logging.info(f'解析后的响应数据: {data}')

            # Extracting data from the response
            stats = data.get('data', {})
            message = (
                f"当前带宽（N分钟峰值）：{stats.get('minutelyPeekBandwidthBytes', 'N/A')} bytes\n"
                f"当天带宽峰值：{stats.get('dailyPeekBandwidthBytes', 'N/A')} bytes\n"
                f"当月带宽峰值：{stats.get('monthlyPeekBandwidthBytes', 'N/A')} bytes\n"
                f"上个月带宽峰值：{stats.get('lastMonthlyPeekBandwidthBytes', 'N/A')} bytes\n"
                f"当天独立IP：{stats.get('dailyCountIPs', 'N/A')}\n"
                f"当天流量：{stats.get('dailyTrafficBytes', 'N/A')} bytes\n"
                f"带宽百分位数：{stats.get('bandwidthPercentile', 'N/A')}\n"
            )
            await update.message.reply_text(message)
        except ValueError:
            await update.message.reply_text('解析响应失败，返回的不是有效的JSON格式。')
    else:
        await update.message.reply_text(f'获取统计数据失败，状态码：{response.status_code}，响应内容：{response.text}')

def main():
    app = ApplicationBuilder().token(API_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("config", config))
    app.add_handler(CommandHandler("token", get_AccessToken))
    app.add_handler(CommandHandler("composeServerStatBoard", get_ServerStatBoard))  # New handler

    app.run_polling()

if __name__ == '__main__':
    main()
