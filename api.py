import os
import sys
import time
import datetime
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile, Query, HTTPException,Form
from fastapi.responses import JSONResponse, Response
from CH34XRelay import CH341Relay

# Get the current script's directory
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory by going one level up
parent_dir = os.path.dirname(current_dir)
# Add the parent directory to sys.path
sys.path.append(parent_dir)
# Get the parent directory by going one level up
parent_dir = os.path.dirname(parent_dir)
# Add the parent directory to sys.path
sys.path.append(parent_dir)

VERSION = '1.0.0'

gateCtl = CH341Relay()

app = FastAPI(title="Wecode Gate-Machine API", version=VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该指定具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/gate-open")
async def gate_open():
    try:
        ok = gateCtl.open_channel(1)
        if not ok:
            return {
                "code": 202,
                'msg': "打开闸机失败"
            }
        time.sleep(0.2)
        gateCtl.close_channel(1)
        return {"code": 200, "msg": "打开闸机成功"}
    except Exception as e:
        return {
            "code": 202,
            'data': '',
            'msg': f"打开闸机失败: {str(e)}"
        }

@app.get("/gate-close")
async def gate_close():
    try:
        ok = gateCtl.open_channel(2)
        if not ok:
            return {
                "code": 202,
                'msg': "关闭闸机失败"
            }
        time.sleep(0.2)
        gateCtl.close_channel(2)
        return {"code": 200, "msg": "关闭闸机成功"}
    except Exception as e:
        return {
            "code": 202,
            'data': '',
            'msg': f"关闭闸机失败: {str(e)}"
        }

@app.get("/version")
async def version():
    return JSONResponse(
        status_code=200,
        content={"version": VERSION}
    )

if __name__ == "__main__":
    import uvicorn
    
    # 启动配置（支持多进程）
    uvicorn.run(
        app="api:app",
        host="0.0.0.0",
        port=5153,
        workers=1, # os.cpu_count() or 4,  # 自动获取CPU核心数
        log_level="info",
        timeout_keep_alive=300
    )