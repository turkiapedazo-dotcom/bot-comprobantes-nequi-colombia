#!/usr/bin/env python3
import os
import subprocess
import sys

def upload_file(local_path, remote_path):
    """Upload a single file to the server"""
    try:
        cmd = [
            'scp', '-o', 'StrictHostKeyChecking=no',
            local_path,
            f'root@5.189.147.111:{remote_path}'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Uploaded {local_path}")
            return True
        else:
            print(f"❌ Failed to upload {local_path}: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error uploading {local_path}: {str(e)}")
        return False

def main():
    # List of HTML files to upload
    html_files = [
        "vouchers_html/1_nequi_a_nequi (2).html",
        "vouchers_html/2_llave_breb (2).html", 
        "vouchers_html/4_bancolombia (2).html",
        "vouchers_html/5_envio_recibido (2).html",
        "vouchers_html/6_qr_vouch_pago_qr (2).html"
    ]
    
    print("🔧 Uploading fixed HTML templates with corrected date formatting...")
    
    success_count = 0
    for html_file in html_files:
        if os.path.exists(html_file):
            remote_path = f"/root/botnequicolfree/{html_file}"
            if upload_file(html_file, remote_path):
                success_count += 1
        else:
            print(f"❌ File not found: {html_file}")
    
    print(f"\n📊 Upload Summary: {success_count}/{len(html_files)} files uploaded successfully")
    
    if success_count == len(html_files):
        print("\n🎉 All HTML templates uploaded successfully!")
        print("✨ Date formatting issue has been fixed in all templates")
        print("💰 Money formatting already works correctly (20.000,00 format)")
        print("\n🚀 The high-quality vouchers should now show proper dates!")
    else:
        print(f"\n⚠️  Only {success_count} out of {len(html_files)} files uploaded")

if __name__ == "__main__":
    main()