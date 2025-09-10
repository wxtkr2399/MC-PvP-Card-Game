from zhipuai import ZhipuAI

api_key = "375c50eab568482cb3e97692486a3bd2.EhMFaiUBrWoaW4ze"
client = ZhipuAI(api_key=api_key)
model = "chatglm_std" # 模型版本

def chat(text):
    # 设置模型和对话内容
    messages = [{"role": "user", "content": text}]
    # 发起请求
    response = client.chat.completions.create(
    model=model,
    messages=messages
    )
    # 输出结果
    return response.choices[0].message.content

def chat_by_context(context):
    # 设置模型和对话内容
    messages = context
    # 发起请求
    response = client.chat.completions.create(
    model=model,
    messages=messages
    )
    # 输出结果
    return response.choices[0].message.content