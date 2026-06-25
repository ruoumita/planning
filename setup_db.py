"""
Script CLI để tạo bảng và seed dữ liệu mẫu.
Chạy: python setup_db.py

Yêu cầu: DATABASE_URL trong .env hoặc biến môi trường.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

from utils.database import create_all_tables, get_database_url
from utils.auth import create_user, hash_password

def main():
    db_url = get_database_url()
    if not db_url:
        print("❌ DATABASE_URL chưa được cấu hình. Thêm vào file .env trước.")
        sys.exit(1)

    print(f"📡 Kết nối: {db_url[:40]}...")

    # Tạo bảng
    ok, msg = create_all_tables()
    if not ok:
        print(f"❌ {msg}")
        sys.exit(1)
    print(f"✅ {msg}")

    # Seed user mẫu
    sample_users = [
        {
            "email":         "admin.dp@company.com",
            "full_name":     "Admin DP",
            "plain_password":"Admin123!",
            "business_role": "DP",
            "system_role":   "ADMIN",
        },
        {
            "email":         "member.sp@company.com",
            "full_name":     "Member SP",
            "plain_password":"Member123!",
            "business_role": "SP",
            "system_role":   "MEMBER",
        },
        {
            "email":         "viewer@company.com",
            "full_name":     "Viewer User",
            "plain_password":"Viewer123!",
            "business_role": "DP",
            "system_role":   "VIEWER",
        },
    ]

    print("\n👥 Tạo tài khoản mẫu:")
    for u in sample_users:
        ok, msg = create_user(
            u["email"], u["full_name"], u["plain_password"],
            u["business_role"], u["system_role"]
        )
        status = "✅" if ok else "⚠️ (có thể đã tồn tại)"
        print(f"  {status} {u['email']} | {u['plain_password']} | {u['business_role']}/{u['system_role']}")

    print("\n✅ Hoàn tất. Đổi mật khẩu sau khi đăng nhập lần đầu!")
    print("\n📋 Tài khoản mẫu:")
    for u in sample_users:
        print(f"  Email: {u['email']:35s}  Password: {u['plain_password']:15s}  Role: {u['business_role']}/{u['system_role']}")


if __name__ == "__main__":
    main()
