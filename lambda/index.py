# lambda/index.py
import json
import os
import re  # 正規表現モジュールをインポート
import urllib.request
import urllib.error

# FastAPI サーバーのURL
FASTAPI_URL = os.environ.get("FASTAPI_URL", "https://5f0f-34-125-90-180.ngrok-free.app/generate")

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))
        
        # Cognitoで認証されたユーザー情報を取得
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")
        
        # リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])
        
        print("Processing message:", message)
        
        # FastAPIサーバーに送信するリクエストデータの構築
        request_payload = {
            "messages": conversation_history.copy(),
            "user_message": message,
            "max_new_tokens": 512,
            "do_sample": True,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        # ユーザーメッセージを追加（会話履歴はすでに含まれている）
        request_payload["messages"].append({
            "role": "user",
            "content": message
        })
        
        print("Calling FastAPI server with payload:", json.dumps(request_payload))
        
        # HTTPリクエストの準備
        headers = {
            "Content-Type": "application/json"
        }
        
        # JSONデータをエンコード
        json_data = json.dumps(request_payload).encode("utf-8")
        
        # FastAPIサーバーにPOSTリクエストを送信
        req = urllib.request.Request(
            FASTAPI_URL,
            data=json_data,
            headers=headers,
            method="POST"
        )
        
        # レスポンスを取得して処理
        with urllib.request.urlopen(req) as response:
            response_body = json.loads(response.read().decode("utf-8"))
        
        print("FastAPI response:", json.dumps(response_body, default=str))
        
        # 応答の検証
        if "generated_text" not in response_body:
            raise Exception("No response content from the model")
        
        # アシスタントの応答を取得
        assistant_response = response_body["generated_text"]
        
        # アシスタントの応答を会話履歴に追加
        updated_history = request_payload["messages"].copy()
        updated_history.append({
            "role": "assistant",
            "content": assistant_response
        })
        
        # 成功レスポンスの返却
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": updated_history
            })
        }
        
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": f"HTTP Error: {e.code} - {e.reason}"
            })
        }
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": f"URL Error: {e.reason}"
            })
        }
    except Exception as error:
        print("Error:", str(error))
        
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }
