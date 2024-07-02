import os
import sys
import time
import json
import random
import requests
import argparse
from json import dumps as dp, loads as ld
from datetime import datetime
from colorama import init, Fore, Style
from urllib.parse import unquote, parse_qs
from base64 import b64decode

init(autoreset=True)

merah = Fore.LIGHTRED_EX
putih = Fore.LIGHTWHITE_EX
hijau = Fore.LIGHTGREEN_EX
kuning = Fore.LIGHTYELLOW_EX
biru = Fore.LIGHTBLUE_EX
reset = Style.RESET_ALL
hitam = Fore.LIGHTBLACK_EX


class BlumTod:
    def __init__(self):
        self.base_headers = {
            "accept": "application/json, text/plain, */*",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
            "content-type": "application/json",
            "origin": "https://telegram.blum.codes",
            "x-requested-with": "org.telegram.messenger",
            "sec-fetch-site": "same-site",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://telegram.blum.codes/",
            "accept-encoding": "gzip, deflate",
            "accept-language": "en,en-US;q=0.9",
        }
        self.garis = putih + "~" * 50

    def renew_access_token(self, tg_data):
        headers = self.base_headers.copy()
        data = dp(
            {
                "query": tg_data,
            }
        )
        headers["Content-Length"] = str(len(data))
        url = "https://gateway.blum.codes/v1/auth/provider/PROVIDER_TELEGRAM_MINI_APP"
        res = self.http(url, headers, data)
        if "token" not in res.json().keys():
            self.log(f"{merah}'token' tidak ditemukan dalam respons, periksa data Anda !!")
            return False

        access_token = res.json()["token"]["access"]
        self.log(f"{hijau}Berhasil mendapatkan access token ")
        return access_token

    def solve_task(self, access_token):
        url_task = "https://game-domain.blum.codes/api/v1/tasks"
        headers = self.base_headers.copy()
        headers["Authorization"] = f"Bearer {access_token}"
        res = self.http(url_task, headers)
        for task in res.json():
            task_id = task["id"]
            task_title = task["title"]
            task_status = task["status"]
            if task_status == "NOT_STARTED":
                url_start = (
                    f"https://game-domain.blum.codes/api/v1/tasks/{task_id}/start"
                )
                res = self.http(url_start, headers, "")
                if "message" in res.text:
                    continue

                url_claim = (
                    f"https://game-domain.blum.codes/api/v1/tasks/{task_id}/claim"
                )
                res = self.http(url_claim, headers, "")
                if "message" in res.text:
                    continue

                status = res.json()["status"]
                if status == "CLAIMED":
                    self.log(f"{hijau}Berhasil menyelesaikan tugas {task_title} !")
                    continue

            self.log(f"{kuning}Tugas {task_title} sudah diselesaikan sebelumnya!")

    def claim_farming(self, access_token):
        url = "https://game-domain.blum.codes/api/v1/farming/claim"
        headers = self.base_headers.copy()
        headers["Authorization"] = f"Bearer {access_token}"
        res = self.http(url, headers, "")
        balance = res.json()["availableBalance"]
        self.log(f"{hijau}Saldo setelah klaim: {balance}")
        return

    def get_balance(self, access_token, only_show_balance=False):
        url = "https://game-domain.blum.codes/api/v1/user/balance"
        headers = self.base_headers.copy()
        headers["Authorization"] = f"Bearer {access_token}"
        res = self.http(url, headers)
        balance = res.json()["availableBalance"]
        self.log(f"{hijau}Saldo: {putih}{balance}")
        if only_show_balance:
            return
        timestamp = round(res.json()["timestamp"] / 1000)
        if "farming" not in res.json().keys():
            return False, "not_started"
        end_farming = round(res.json()["farming"]["endTime"] / 1000)
        if timestamp > end_farming:
            self.log(f"{hijau}Saatnya untuk klaim farming sekarang!")
            return True, end_farming

        self.log(f"{kuning}Belum saatnya untuk klaim farming!")
        end_date = datetime.fromtimestamp(end_farming)
        self.log(f"{hijau}Berakhirnya farming: {putih}{end_date}")
        return False, end_farming

    def start_farming(self, access_token):
        url = "https://game-domain.blum.codes/api/v1/farming/start"
        headers = self.base_headers.copy()
        headers["Authorization"] = f"Bearer {access_token}"
        res = self.http(url, headers, "")
        end = res.json()["endTime"]
        end_date = datetime.fromtimestamp(end / 1000)
        self.log(f"{hijau}Memulai farming berhasil!")
        self.log(f"{hijau}Berakhirnya farming: {putih}{end_date}")
        return round(end / 1000)

    def get_friend(self, access_token):
        url = "https://gateway.blum.codes/v1/friends/balance"
        headers = self.base_headers.copy()
        headers["Authorization"] = f"Bearer {access_token}"
        res = self.http(url, headers)
        can_claim = res.json()["canClaim"]
        limit_invite = res.json()["limitInvitation"]
        amount_claim = res.json()["amountForClaim"]
        ref_code = res.json()["referralToken"]
        self.log(f"{putih}Batas undangan: {hijau}{limit_invite}")
        self.log(f"{hijau}Jumlah klaim: {putih}{amount_claim}")
        self.log(f"{putih}Bisa klaim: {hijau}{can_claim}")
        if can_claim:
            url_claim = "https://gateway.blum.codes/v1/friends/claim"
            res = self.http(url_claim, headers, "")
            if "claimBalance" in res.json().keys():
                self.log(f"{hijau}Berhasil klaim bonus referral!")
                return
            self.log(f"{merah}Gagal klaim bonus referral!")
            return

    def checkin(self, access_token):
        url = "https://game-domain.blum.codes/api/v1/daily-reward?offset=-420"
        headers = self.base_headers.copy()
        headers["Authorization"] = f"Bearer {access_token}"
        res = self.http(url, headers)
        if res.status_code == 404:
            self.log(f"{kuning}Sudah check-in hari ini!")
            return
        res = self.http(url, headers, "")
        if "ok" in res.text.lower():
            self.log(f"{hijau}Berhasil check-in hari ini!")
            return

        self.log(f"{merah}Gagal check-in hari ini!")
        return

    def playgame(self, access_token):
        url_play = "https://game-domain.blum.codes/api/v1/game/play"
        url_claim = "https://game-domain.blum.codes/api/v1/game/claim"
        url_balance = "https://game-domain.blum.codes/api/v1/user/balance"
        headers = self.base_headers.copy()
        headers["Authorization"] = f"Bearer {access_token}"
        res = self.http(url_balance, headers)
        play = res.json()["playPasses"]
        self.log(f"{hijau}Anda memiliki {putih}{play}{hijau} tiket game")
        for i in range(play):
            res = self.http(url_play, headers, "")
            game_id = res.json()["gameId"]
            self.countdown(30)
            point = random.randint(self.MIN_WIN, self.MAX_WIN)
            data = json.dumps({"gameId": game_id, "points": point})
            res = self.http(url_claim, headers, data)
            if "points" in res.text:
                self.log(f"{hijau}Berhasil main game, mendapatkan {putih}{point} {hijau}poin")
                continue

            self.log(f"{merah}Gagal main game, cobalah lagi nanti")

    def data_parsing(self, text):
        result = parse_qs(unquote(text)).items()
        return dict(result)

    def decode_access_token(self, access_token):
        payload = access_token.split(".")[1]
        padding = 4 - len(payload) % 4
        payload += "=" * padding
        decode = b64decode(payload)
        return json.loads(decode)

    def countdown(self, second, message="please wait"):
        while second:
            mins, secs = divmod(second, 60)
            timer = f"{kuning}{message}: {putih}{mins:02d}:{secs:02d}"
            print(timer, end="\r")
            time.sleep(1)
            second -= 1

    def http(self, url, headers, data=None, max_retry=3):
        for i in range(max_retry):
            try:
                res = (
                    requests.post(url, headers=headers, data=data)
                    if data
                    else requests.get(url, headers=headers)
                )
                return res
            except Exception as e:
                self.log(f"{merah}error {putih}{str(e)}")
                self.countdown(3, "error")

    def log(self, message):
        print(f"{putih}[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def main(self, *args, **kwargs):
        if not os.path.isfile("tokens.json"):
            self.log(f"{merah}file tokens.json is not found")
            return

        with open("tokens.json") as r:
            data_tokens = json.load(r)
            self.MIN_WIN = data_tokens["MIN_WIN"]
            self.MAX_WIN = data_tokens["MAX_WIN"]
            tokens = data_tokens["data"]

        if not os.path.isfile("auth_failed.json"):
            with open("auth_failed.json", "w") as w:
                json.dump({"data": []}, w, indent=4)

        with open("auth_failed.json") as r:
            data_auth_failed = json.load(r)
            auth_failed = data_auth_failed["data"]

        for token in tokens:
            telegram_data = token["telegram_data"]
            name = token["name"]
            tg_data = self.data_parsing(telegram_data)
            self.log(f"{biru}run {putih}{name} ...")
            access_token = self.renew_access_token(tg_data)
            if not access_token:
                self.log(f"{merah}failed get access token {putih}{name}")
                auth_failed.append(token)
                continue

            decode = self.decode_access_token(access_token)
            expired = decode["exp"]
            now = int(time.time())
            delta = expired - now
            self.log(f"{hijau}access token life: {putih}{round(delta/3600, 2)} hour")
            self.checkin(access_token)
            status, end_farming = self.get_balance(access_token)
            if status:
                self.claim_farming(access_token)
                self.start_farming(access_token)
            self.solve_task(access_token)
            self.playgame(access_token)
            self.get_friend(access_token)

        if auth_failed:
            with open("auth_failed.json", "w") as w:
                json.dump(data_auth_failed, w, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--method", default="main", help="method to run")
    args = parser.parse_args()
    method = args.method
    BlumTod().__getattribute__(method)()
