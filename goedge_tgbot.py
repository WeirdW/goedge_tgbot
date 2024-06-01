import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests

# 配置日志记录
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
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
    
    api_url, type, accessKeyId, accessKey = context.args
    user_id = update.message.from_user.id
    user_edge_info[user_id] = {'api_url': api_url, 'type': type, 'accessKeyId': accessKeyId, 'accessKey': accessKey}
    await update.message.reply_text('配置成功！请使用 /token 获取获取AccessToken。')

async def get_AccessToken(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id not in user_edge_info:
        await update.message.reply_text('请先使用 /config 命令配置你的API节点。')
        return

    api_url = user_edge_info[user_id]['api_url']
    type = user_edge_info[user_id]['type']
    accessKeyId = user_edge_info[user_id]['accessKeyId']
    accessKey = user_edge_info[user_id]['accessKey']
    
    data= {
    "type": type,
    "accessKeyId": accessKeyId,
    "accessKey": accessKey
    }
    json_data=json.dumps(data)
    headers={'Content-Type':'application/json'}
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

            message = f"AccessToken：\n{token}"
            await update.message.reply_text(message)
        except ValueError:
            await update.message.reply_text('解析响应失败，返回的不是有效的JSON格式。')
    else:
        await update.message.reply_text(f'获取token失败，状态码：{response.status_code}，响应内容：{response.text}')

def main():
    app = ApplicationBuilder().token(API_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("config", config))
    app.add_handler(CommandHandler("token", get_AccessToken))

    app.run_polling()

if __name__ == '__main__':
    main()
