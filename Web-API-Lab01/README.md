# Lab 1: Introduction, HTTP & Web API (DGT01 1020)
คู่มือการติดตั้งและรันโปรแกรม Network Programming Lab 01

## 🛠️ ขั้นตอนการเตรียมเครื่อง (Setup & venv)
1. **สร้าง Virtual Environment (ครั้งแรกครั้งเดียว)**
   ```powershell
   python -m venv venv
   ```

2. **Activate venv และติดตั้ง Library**
   *   **Windows (PowerShell):**
       ```powershell
       .\venv\Scripts\Activate.ps1
       pip install requests fastapi uvicorn
       ```
   *   **Command Prompt (cmd):**
       ```cmd
       venv\Scripts\activate.bat
       pip install requests fastapi uvicorn
       ```

## 🚀 ขั้นตอนการรัน Lab 01 แต่ละ Task
*(ต้อง Activate venv ก่อนรันเสมอ)*
รันไฟล์ Python ทีละเครื่องทาง Terminal:
*   **Task 1: GitHub User Info**
    ```powershell
    python task1.py
    ```
*   **Task 2: Top Python Repos**
    ```powershell
    python task2.py
    ```
*   **Task 3: Error Handling Test**
    ```powershell
    python lab3.py
    ```
*   **Task 4: Country Search**
    ```powershell
    python lab4.py
    ```

---

## 🌐 ขั้นตอนการรัน FastAPI (Task พิเศษ)
เพื่อทดสอบ API ผ่านหน้าเว็บ (Swagger UI):

1. **รัน Server**
   ```powershell
   python main.py
   ```
2. **การเข้าใช้งาน**
   *   **จากเครื่องตัวเอง (Local):** [http://localhost:8000/docs](http://localhost:8000/docs)
   *   **จากเครื่องอื่นในวง Wi-Fi เดียวกัน:** แจ้ง IP ของคุณให้เพื่อน เช่น `http://[IP_ADDRESS]:8000/docs`

---
> [!TIP]
> **หากเกิด Error `[Errno 10048]`**
> แสดงว่าพอร์ต 8000 มีการค้างอยู่ ให้ปิด Terminal เดิมและเปิดใหม่ หรือกด `Ctrl+C` เพื่อหยุดการรันเดิมก่อนเสมอ
