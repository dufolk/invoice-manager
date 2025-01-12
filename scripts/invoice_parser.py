import base64
import urllib
import requests
from scripts.config import API_KEY, SECRET_KEY

def get_invoice_info(base64_data, file_type):
    """
    解析发票信息
    :param base64_data: 文件的 base64 编码
    :param file_type: 文件类型 (pdf/jpg/jpeg/png)
    :return: API 响应结果
    """
    url = "https://aip.baidubce.com/rest/2.0/ocr/v1/vat_invoice?access_token=" + get_access_token()
    base64_data = urllib.parse.quote_plus(base64_data)
    # 根据文件类型构建不同的参数
    if file_type == 'pdf':
        payload = f"pdf_file={base64_data}"
    else:  # 图片文件
        payload = f"image={base64_data}"
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    }
    
    response = requests.request("POST", url, headers=headers, data=payload.encode("utf-8"))
    return response.text
    

def get_file_content_as_base64(path, urlencoded=False):
    """
    获取文件base64编码
    :param path: 文件路径
    :param urlencoded: 是否对结果进行urlencoded 
    :return: base64编码信息
    """
    with open(path, "rb") as f:
        content = base64.b64encode(f.read()).decode("utf8")
        if urlencoded:
            content = urllib.parse.quote_plus(content)
    return content

def get_access_token():
    """
    使用 AK，SK 生成鉴权签名（Access Token）
    :return: access_token，或是None(如果错误)
    """
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": API_KEY, "client_secret": SECRET_KEY}
    return str(requests.post(url, params=params).json().get("access_token"))

if __name__ == '__main__':
    print(get_invoice_info('/Users/dufolk/test.pdf'))