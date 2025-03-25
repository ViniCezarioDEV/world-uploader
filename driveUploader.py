import os
import shutil
import sys
import re
import gdown
import zipfile
from datetime import datetime, date
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaFileUpload
from colorama import Fore, init, Style

init(autoreset=True)  # Colorama auto-reset

# Configurações
DRIVE_FOLDER = "1QGyK3cJAaQUejn9PyQPiUvdLdKEVaU6Y"
SCOPES = ["https://www.googleapis.com/auth/drive"]

# Caminhos
MINECRAFT_SAVES = os.path.join(os.getenv("APPDATA"), ".minecraft", "saves")
WORLD_NAME = "The_Typical_Solution"
BACKUP_NAME = f"{WORLD_NAME}_Backup_{date.today().strftime('%d-%m-%Y')}"
WORLD_PATH = os.path.join(MINECRAFT_SAVES, WORLD_NAME)
BACKUP_ZIP = os.path.join(MINECRAFT_SAVES, f"{BACKUP_NAME}.zip")


CREDENTIALS_PATH = os.path.join(os.getcwd(), "credentials.json")
TOKEN_PATH = os.path.join(os.getcwd(), "token.json")


def authenticate_drive():
    global CREDENTIALS_PATH, TOKEN_PATH

    print(f"{Fore.CYAN}[LOG]{Fore.WHITE} Verificando credenciais em: {CREDENTIALS_PATH}")  # Verifique o caminho correto
    print(f"{Fore.CYAN}[LOG]{Fore.WHITE} Verificando token em: {TOKEN_PATH}\n")  # Veja onde o token está sendo salvo

    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        try:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

            with open(TOKEN_PATH, "w") as token_file:
                token_file.write(creds.to_json())

        except FileNotFoundError:
            print(f"Erro: Arquivo 'credentials.json' não encontrado em {CREDENTIALS_PATH}")
            input(f' {Fore.CYAN}[LOG] Precione Enter para sair >>>>')

    return build("drive", "v3", credentials=creds)



def zip_world():
    if not os.path.exists(WORLD_PATH):
        print(f"{Fore.RED}[ERRO]{Fore.WHITE} O mundo '{WORLD_NAME}' não foi encontrado!")
        return False

    print(f"{Fore.CYAN}[LOG]{Fore.WHITE} Compactando {WORLD_PATH}...")
    shutil.make_archive(BACKUP_ZIP.replace(".zip", ""), "zip", WORLD_PATH)
    print(f"{Fore.GREEN}[OK]{Fore.WHITE} Mundo compactado!")
    return True


def upload_world():
    if not os.path.exists(BACKUP_ZIP):
        print(f"{Fore.RED}[ERRO]{Fore.WHITE} Arquivo de backup não encontrado!")
        return

    drive_service = authenticate_drive()
    print(f"{Fore.CYAN}[LOG]{Fore.WHITE} Enviando {BACKUP_ZIP} para Google Drive...")

    file_metadata = {"name": os.path.basename(BACKUP_ZIP), "parents": [DRIVE_FOLDER]}
    media = MediaFileUpload(BACKUP_ZIP, resumable=True)
    file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()

    drive_service.permissions().create(fileId=file.get("id"), body={"type": "anyone", "role": "reader"}).execute()
    print(f"{Fore.GREEN}[OK]{Fore.WHITE} Upload concluído! Link: https://drive.google.com/file/d/{file.get('id')}/view")


def download_world():
    drive_service = authenticate_drive()
    results = drive_service.files().list(q=f"'{DRIVE_FOLDER}' in parents", fields="files(id, name)").execute()
    files = results.get("files", [])

    if not files:
        print(f"{Fore.RED}[ERRO]{Fore.WHITE} Nenhum backup encontrado!")
        return

    try:
        latest_backup = max(files, key=lambda f: datetime.strptime(re.findall(r"\d{2}-\d{2}-\d{4}", f["name"])[0], "%d-%m-%Y"))
    except (IndexError, ValueError):
        print(f"{Fore.RED}[ERRO]{Fore.WHITE} Nenhum backup válido encontrado no Google Drive!")
        return

    file_id, file_name = latest_backup["id"], latest_backup["name"]

    print(f"{Fore.CYAN}[LOG]{Fore.WHITE} Baixando {file_name}...")
    gdown.download(f"https://drive.google.com/uc?id={file_id}", BACKUP_ZIP, quiet=False)

    extract_world()


def extract_world():
    extract_path = os.path.join(MINECRAFT_SAVES, WORLD_NAME)

    if os.path.exists(extract_path):
        shutil.rmtree(extract_path)

    with zipfile.ZipFile(BACKUP_ZIP, "r") as zip_ref:
        zip_ref.extractall(extract_path)

    os.remove(BACKUP_ZIP)
    print(f"{Fore.GREEN}[OK]{Fore.WHITE} Mundo restaurado em {extract_path}")


def main():
    print(f"""{Fore.CYAN}{Style.BRIGHT}
     __      __  _   _  | |__   (_)   __ _    __| |
     \ \ /\ / / | | | | | '_ \  | |  / _` |  / _` |
      \ V  V /  | |_| | | |_) | | | | (_| | | (_| |
       \_/\_/    \__,_| |_.__/  |_|  \__, |  \__,_| 
                                     |___/ {Fore.WHITE}{Style.NORMAL} (World-Uploader-Based-In-Google-Drive)""")

    while True:
        print(f"""
        {Fore.CYAN}[1]{Fore.WHITE} Subir mundo para o Drive
        {Fore.CYAN}[2]{Fore.WHITE} Baixar mundo do Drive
        {Fore.CYAN}[3]{Fore.WHITE} Sair do programa""")
        choice = input(">>> ")
        if choice == "1":
            if zip_world():
                upload_world()
        elif choice == "2":
            download_world()
        elif choice == "3":
            sys.exit()
        else:
            print(f"{Fore.RED}[ERRO]{Fore.WHITE} Opção inválida!")


if __name__ == "__main__":
    main()
