import json
import os

import aiohttp

SAFETY = [
    {"category": c, "threshold": "BLOCK_NONE"}
    for c in (
        "HARM_CATEGORY_HATE_SPEECH",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "HARM_CATEGORY_DANGEROUS_CONTENT",
        "HARM_CATEGORY_HARASSMENT",
    )
]

ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent?key={key}"
)

DEFAULT_MODEL = "gemini-3.5-flash-lite"
DEFAULT_MAX_TOKENS = 2048
DEFAULT_THINKING = None

RETRY_STATUS = (400, 401, 403, 429, 500, 502, 503, 504)


def _clean(key: str) -> str:
    return key.strip().strip("=").strip()


class GeminiError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


class GeminiClient:
    def __init__(self, keys_env="GEMINI_API_KEYS", model_env="GEMINI_MODEL",
                 keys_file="app_io/input/gemini_keys.txt"):
        self.keys_env = keys_env
        self.model_env = model_env
        self.keys_file = keys_file
        self._index = 0

    def keys(self):
        raw = os.environ.get(self.keys_env, "")
        keys = [_clean(k) for k in raw.replace(",", "\n").splitlines()]
        if not any(keys) and os.path.exists(self.keys_file):
            try:
                with open(self.keys_file, "r", encoding="utf-8") as f:
                    keys = [
                        _clean(k)
                        for k in f.read().replace(",", "\n").splitlines()
                    ]
            except Exception:
                keys = []
        return [k for k in keys if k]

    @property
    def model(self):
        return os.environ.get(self.model_env, "").strip() or DEFAULT_MODEL

    def masked(self):
        out = []
        for k in self.keys():
            out.append(f"{k[:6]}…{k[-4:]}" if len(k) > 12 else "…")
        return out

    def _body(self, contents, system, temperature, max_tokens, thinking):
        gen = {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }
        if thinking is not None:
            gen["thinkingConfig"] = {"thinkingBudget": thinking}
        body = {
            "contents": contents,
            "safetySettings": SAFETY,
            "generationConfig": gen,
        }
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        return body

    async def _call(self, key, body, timeout):
        url = ENDPOINT.format(model=self.model, key=key)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=body) as res:
                return res.status, await res.text()

    async def generate(self, contents, system=None, temperature=0.9,
                       max_tokens=DEFAULT_MAX_TOKENS,
                       thinking=DEFAULT_THINKING):
        keys = self.keys()
        if not keys:
            raise GeminiError(0, "APIキーが未設定です")

        timeout = aiohttp.ClientTimeout(total=45)
        last = None
        variants = [thinking, None] if thinking is not None else [None]

        for th in variants:
            body = self._body(contents, system, temperature, max_tokens, th)
            for i in range(len(keys)):
                key = keys[(self._index + i) % len(keys)]
                try:
                    status, text = await self._call(key, body, timeout)
                except Exception as e:
                    last = GeminiError(0, str(e))
                    continue

                if status == 200:
                    data = json.loads(text)
                    self._index = (self._index + i) % len(keys)
                    cand = (data.get("candidates") or [{}])[0]
                    parts = (cand.get("content") or {}).get("parts") or []
                    out = "".join(
                        p.get("text", "") for p in parts if not p.get("thought")
                    )
                    return out, cand.get("finishReason")

                print(f"gemini {status}: {text[:400]}")
                last = GeminiError(status, text[:400])

                if status in RETRY_STATUS:
                    continue
                raise last

        raise last or GeminiError(0, "生成に失敗しました")