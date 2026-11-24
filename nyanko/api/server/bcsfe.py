import json
import random
import os
import uuid
import datetime

from app_io.input import PRICE_OVERRIDES, ORDER_LOG

try:
    import bcsfe.core as core
    import bcsfe.cli.edits.max_all as max_all
    import bcsfe.cli.edits.map as map_edit
    from bcsfe.core.game.gamoto.gamatoto import Helper, Helpers
    from bcsfe.core.game.gamoto.ototo import Cannons, CastleRecipeUnlock
    BCSFE_AVAILABLE = True
except ImportError:
    core = None
    max_all = None
    map_edit = None
    BCSFE_AVAILABLE = False

ITEM_CONFIG = {
    "catfood_50000": {"label": "猫缶 50,000個", "price": 0, "cat": "resource"},
    "xp_max": {"label": "XP 99,999,999", "price": 0, "cat": "resource"},
    "np_max": {"label": "NP 9,999", "price": 0, "cat": "resource"},
    "nyan_ticket_999": {"label": "にゃんチケット 999枚", "price": 0, "cat": "resource"},
    "rare_tickets_999": {"label": "レアチケット 999枚", "price": 0, "cat": "resource"},
    "platinum_29": {"label": "プラチナチケット 29枚", "price": 0, "cat": "resource"},
    "legend_29": {"label": "レジェンドチケット 29枚", "price": 0, "cat": "resource"},
    "platinum_shard_90": {"label": "プラチナのかけら 90個", "price": 0, "cat": "resource"},
    "leadership_999": {"label": "リーダーシップ 999個", "price": 0, "cat": "resource"},
    "battle_items_999": {"label": "バトルアイテム全種 999個", "price": 0, "cat": "resource"},
    "matatabi_998": {"label": "マタタビ全種 998個", "price": 0, "cat": "resource"},
    "cats_eye_999": {"label": "キャッツアイ全種 999個", "price": 0, "cat": "resource"},
    "nekovitan_999": {"label": "ネコビタン全種 999個", "price": 0, "cat": "resource"},
    "castle_parts_999": {"label": "城素材全種 999個", "price": 0, "cat": "resource"},
    "event_ticket_999": {"label": "イベントチケット 999枚", "price": 0, "cat": "resource"},
    "honnou_99": {"label": "本能玉全種 99個", "price": 0, "cat": "resource"},
    "dungeon_medal_99": {"label": "地底迷宮メダル全種 99個", "price": 0, "cat": "resource"},
    "all_missions": {"label": "全ミッション完了", "price": 0, "cat": "stage"},
    "main_clear": {"label": "メインステージ全クリア+お宝金", "price": 0, "cat": "stage"},
    "zombie_clear": {"label": "メインゾンビステージ全クリア", "price": 0, "cat": "stage"},
    "old_legend_clear": {"label": "旧レジェンド全クリア", "price": 0, "cat": "stage"},
    "true_legend_clear": {"label": "真レジェンド全クリア", "price": 0, "cat": "stage"},
    "zero_legend_clear": {"label": "零レジェンド全クリア", "price": 0, "cat": "stage"},
    "makai_clear": {"label": "魔界編全クリア", "price": 0, "cat": "stage"},
    "event_clear": {"label": "イベントステージ全クリア", "price": 0, "cat": "stage"},
    "clear_nyanko_tower": {"label": "にゃんこ塔全クリア", "price": 0, "cat": "stage"},
    "all_char_unlock": {"label": "全キャラ開放", "price": 0, "cat": "chara"},
    "error_char_delete": {"label": "エラーキャラ削除", "price": 0, "cat": "chara"},
    "all_char_lv_max": {"label": "全キャラLvMAX", "price": 0, "cat": "chara"},
    "all_char_max_form": {"label": "全キャラ最大形態", "price": 0, "cat": "chara"},
    "all_honnou_max": {"label": "全キャラ本能全開放", "price": 0, "cat": "chara"},
    "telop_delete": {"label": "開放テロップ削除", "price": 0, "cat": "etc"},
    "slot_max": {"label": "編成スロット数最大拡張", "price": 0, "cat": "etc"},
    "medal_all": {"label": "にゃんこメダル全開放", "price": 0, "cat": "etc"},
    "enemy_book_all": {"label": "敵キャラ図鑑全開放", "price": 0, "cat": "etc"},
    "user_rank_all": {"label": "ユーザーランク報酬全受取", "price": 0, "cat": "etc"},
    "playtime_max": {"label": "プレイ時間カンスト", "price": 0, "cat": "etc"},
    "gold_pass": {"label": "ゴールド会員化", "price": 0, "cat": "etc"},
    "facility_max": {"label": "施設LvMAX", "price": 0, "cat": "etc"},
    "gamatoto_max": {"label": "ガマトトLvMAX", "price": 0, "cat": "etc"},
    "gamatoto_legend": {"label": "ガマトト助手全員レジェンド", "price": 0, "cat": "etc"},
    "ad_free": {"label": "ランクアップセール非表示", "price": 0, "cat": "etc"},
    "ototo_max": {"label": "オトート全城強化LvMAX", "price": 0, "cat": "etc"},
    "shrine_max": {"label": "にゃんこ神社LvMAX", "price": 0, "cat": "etc"},
}


def get_items_by_cat(cat):
    return {k: v for k, v in ITEM_CONFIG.items() if v["cat"] == cat}


def load_json(path, default=None):
    if default is None:
        default = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_price(item_key, guild_id=None):
    overrides = load_json(PRICE_OVERRIDES, {})
    if guild_id and str(guild_id) in overrides:
        if item_key in overrides[str(guild_id)]:
            return overrides[str(guild_id)][item_key]
    return ITEM_CONFIG[item_key]["price"]


def set_price(item_key, price, guild_id):
    try:
        overrides = load_json(PRICE_OVERRIDES, {})
        gid = str(guild_id)
        if gid not in overrides:
            overrides[gid] = {}
        overrides[gid][item_key] = price
        save_json(PRICE_OVERRIDES, overrides)
        return True
    except Exception as e:
        print(f"set_price error: {e}")
        return False


def log_order(user_id, items, service_type="normal"):
    orders = load_json(ORDER_LOG, [])
    orders.append({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "items": items,
        "type": service_type,
        "time": datetime.datetime.now().isoformat()
    })
    save_json(ORDER_LOG, orders)


class BCSFEAPI:
    def __init__(self, cc: str = "jp"):
        self.save_file = None
        self.handler = None
        self.cc = core.CountryCode.from_code(cc) if BCSFE_AVAILABLE else None
        self.gv = None
        if BCSFE_AVAILABLE:
            self._init_core()

    def _init_core(self):
        try:
            root = os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))))
            data_dir = core.Path(os.path.join(root, "data", "bcsfe"))
            data_dir.generate_dirs()
            core.set_data_dir_path(data_dir)
            core.set_config_path(data_dir.add("config.json"))
            core.set_log_path(data_dir.add("log.txt"))
            core.core_data.init_data()
        except Exception as e:
            print(f"core init error: {type(e).__name__}: {e}")

    # ---------- 取得 / アップロード ----------

    def _latest_gv(self):
        if self.gv is not None:
            return self.gv
        versions = None
        try:
            versions = core.GameDataGetter.possible_versions(self.cc)
        except Exception:
            pass
        if versions:
            self.gv = core.GameVersion.from_string(versions[0])
        else:
            self.gv = core.GameVersion.from_string("14.1.0")
        return self.gv

    async def download_save(self, transfer_code: str, pin: str) -> dict:
        if not BCSFE_AVAILABLE:
            return {"success": False, "error": "bcsfe がインストールされていません"}
        try:
            self.gv = self._latest_gv()
            handler, _err = core.ServerHandler.from_codes(
                transfer_code, pin, self.cc, self.gv, print=False
            )
            if handler is None:
                return {"success": False,
                        "error": "引継ぎコードまたはPINが正しくありません"}
            self.handler = handler
            self.save_file = handler.save_file
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": f"{type(e).__name__}: {e}"}

    async def upload_save(self) -> dict:
        if not self.handler or not self.save_file:
            return {"success": False, "error": "セーブデータが読み込まれていません"}
        try:
            codes = self.handler.get_codes()
            if codes is None:
                return {"success": False, "error": "アップロードに失敗しました"}
            transfer_code, pin = codes
            return {"success": True, "transfer_code": transfer_code, "pin": pin}
        except Exception as e:
            return {"success": False, "error": f"{type(e).__name__}: {e}"}

    # ---------- ファイル入出力 ----------

    def load_save(self, save_data: dict) -> bool:
        if not BCSFE_AVAILABLE:
            return False
        try:
            dt = core.Data(json.dumps(save_data).encode("utf-8"))
            self.save_file = core.SaveFile(dt, cc=self.cc)
            return True
        except Exception as e:
            print(f"load_save error: {e}")
            return False

    def load_save_from_file(self, filepath: str) -> bool:
        if not BCSFE_AVAILABLE:
            return False
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return self.load_save(data)
        except Exception as e:
            print(f"load_save_from_file error: {e}")
            return False

    def get_edited_data(self):
        if self.save_file:
            return self.save_file.to_dict()
        return None

    def save_to_file(self, filepath: str) -> bool:
        data = self.get_edited_data()
        if data:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                return True
            except Exception as e:
                print(f"save_to_file error: {e}")
        return False

    # ---------- 編集 ----------

    def apply_edits(self, items: list) -> dict:
        if not self.save_file:
            return {"success": False, "error": "セーブデータが読み込まれていません"}

        sf = self.save_file
        results = {}

        def run(item, fn):
            try:
                fn()
                results[item] = True
            except Exception as e:
                print(f"apply_edits error for {item}: {type(e).__name__}: {e}")
                results[item] = False

        def fill(lst, value):
            if not isinstance(lst, list) or not lst:
                raise ValueError("対象リストが空です")
            for i in range(len(lst)):
                lst[i] = value

        def attr_of(obj, *names):
            for n in names:
                v = getattr(obj, n, None)
                if v is not None:
                    return v
            raise ValueError("属性が見つかりません")

        def clear_chapters(obj, treasure=0, etype=None):
            if isinstance(obj, core.EventChapters):
                if etype is None:
                    raise ValueError("EventChapters \u306b\u306f type \u304c\u5fc5\u8981\u3067\u3059")
                for m in range(obj.get_lengths()[1]):
                    for star in range(obj.get_total_stars(etype, m)):
                        for st in range(obj.get_total_stages(etype, m, star)):
                            try:
                                obj.clear_stage(etype, m, star, st, 1, True)
                            except Exception:
                                pass
                return
            if isinstance(obj, core.StoryChapters):
                for m, ch in enumerate(obj.chapters):
                    for st in range(len(ch.stages)):
                        try:
                            obj.clear_stage(m, st, 1, True)
                        except Exception:
                            pass
                        if treasure:
                            try:
                                obj.set_treasure(m, st, treasure)
                            except Exception:
                                pass
                return
            if isinstance(obj, core.Outbreaks):
                for cid, ch in list(obj.chapters.items()):
                    true_id = cid if cid < 3 else cid - 1
                    for sid in list(ch.outbreaks.keys()):
                        try:
                            obj.clear_outbreak(true_id, sid, True)
                        except Exception:
                            pass
                return
            chapter_data = obj.chapters
            if isinstance(chapter_data, list):
                maps = chapter_data
                clear_stage = obj.clear_stage
            else:
                maps = chapter_data.chapters
                clear_stage = chapter_data.clear_stage
            if not maps:
                raise ValueError("クリア対象のチャプターがありません")
            for m, map_data in enumerate(maps):
                for star, chapter in enumerate(map_data.chapters):
                    for st in range(len(chapter.stages)):
                        clear_stage(m, star, st, 1, True)

        for item in items:
            if item == "catfood_50000":
                run(item, lambda: max_all.max_catfood(sf))
            elif item == "xp_max":
                run(item, lambda: max_all.max_xp(sf))
            elif item == "np_max":
                run(item, lambda: max_all.max_np(sf))
            elif item == "nyan_ticket_999":
                run(item, lambda: max_all.max_normal_tickets(sf))
            elif item == "rare_tickets_999":
                run(item, lambda: max_all.max_rare_tickets(sf))
            elif item == "platinum_29":
                run(item, lambda: max_all.max_plat_tickets(sf))
            elif item == "legend_29":
                run(item, lambda: max_all.max_legend_tickets(sf))
            elif item == "platinum_shard_90":
                run(item, lambda: max_all.max_plat_shards(sf))
            elif item == "leadership_999":
                run(item, lambda: max_all.max_leadership(sf))

            elif item == "battle_items_999":
                run(item, lambda: max_all.max_battle_items(sf))

            elif item == "matatabi_998":
                def _matatabi():
                    fruits = core.Matatabi(sf).matatabi
                    if not fruits:
                        raise ValueError("\u30de\u30bf\u30bf\u30d3\u30c7\u30fc\u30bf\u3092\u53d6\u5f97\u3067\u304d\u307e\u305b\u3093\u3067\u3057\u305f")
                    if len(sf.catfruit) < len(fruits):
                        sf.catfruit += [0] * (len(fruits) - len(sf.catfruit))
                    seeds = [i for i, f in enumerate(fruits) if f.seed]
                    for i in (seeds or list(range(len(fruits)))):
                        sf.catfruit[i] = 998
                run(item, _matatabi)

            elif item == "cats_eye_999":
                run(item, lambda: max_all.max_catseyes(sf))

            elif item == "nekovitan_999":
                run(item, lambda: fill(sf.catfruit, 999))

            elif item == "dungeon_medal_99":
                run(item, lambda: max_all.max_labyrinth_medals(sf))

            elif item == "castle_parts_999":
                def _castle():
                    mats = sf.ototo.base_materials.materials
                    if not mats:
                        raise ValueError("\u57ce\u7d20\u6750\u30c7\u30fc\u30bf\u304c\u3042\u308a\u307e\u305b\u3093")
                    for mat in mats:
                        mat.amount = 999
                run(item, _castle)

            elif item == "event_ticket_999":
                def _event_ticket():
                    try:
                        max_all.max_100_million_ticket(sf)
                    except Exception:
                        fill(attr_of(sf, "lucky_tickets", "event_tickets"), 999)
                run(item, _event_ticket)

            elif item == "honnou_99":
                def _orbs():
                    for i in range(1, 200):
                        try:
                            sf.talent_orbs.set_orb(i, 99)
                        except Exception:
                            pass
                run(item, _orbs)

            elif item == "all_honnou_max":
                def _talent():
                    td = core.TalentData.from_game_data(sf)
                    if td is None:
                        raise ValueError("\u672c\u80fd\u30c7\u30fc\u30bf\u3092\u53d6\u5f97\u3067\u304d\u307e\u305b\u3093\u3067\u3057\u305f")
                    done = 0
                    for cat in sf.cats.get_all_cats():
                        if not cat.talents:
                            continue
                        data = td.get_cat_talents(cat)
                        if data is None:
                            continue
                        _, max_levels, _, ids = data
                        for talent in cat.talents:
                            if talent.id in ids:
                                talent.level = max_levels[ids.index(talent.id)]
                                done += 1
                    if done == 0:
                        raise ValueError("\u672c\u80fd\u3092\u958b\u653e\u3067\u304d\u307e\u305b\u3093\u3067\u3057\u305f")
                run(item, _talent)

            elif item == "all_honnou_max":
                def _talent():
                    td = core.TalentData.from_game_data(sf)
                    if td is None:
                        raise ValueError("\u672c\u80fd\u30c7\u30fc\u30bf\u3092\u53d6\u5f97\u3067\u304d\u307e\u305b\u3093\u3067\u3057\u305f")
                    done = 0
                    for cat in sf.cats.get_all_cats():
                        if not cat.talents:
                            continue
                        data = td.get_cat_talents(cat)
                        if data is None:
                            continue
                        _, max_levels, _, ids = data
                        for talent in cat.talents:
                            if talent.id in ids:
                                talent.level = max_levels[ids.index(talent.id)]
                                done += 1
                    if done == 0:
                        raise ValueError("\u672c\u80fd\u3092\u958b\u653e\u3067\u304d\u307e\u305b\u3093\u3067\u3057\u305f")
                run(item, _talent)

            elif item == "all_honnou_max":
                def _talent():
                    td = core.TalentData.from_game_data(sf)
                    if td is None:
                        raise ValueError("\u672c\u80fd\u30c7\u30fc\u30bf\u3092\u53d6\u5f97\u3067\u304d\u307e\u305b\u3093\u3067\u3057\u305f")
                    done = 0
                    for cat in sf.cats.get_all_cats():
                        if not cat.talents:
                            continue
                        data = td.get_cat_talents(cat)
                        if data is None:
                            continue
                        _, max_levels, _, ids = data
                        for talent in cat.talents:
                            if talent.id in ids:
                                talent.level = max_levels[ids.index(talent.id)]
                                done += 1
                    if done == 0:
                        raise ValueError("\u672c\u80fd\u3092\u958b\u653e\u3067\u304d\u307e\u305b\u3093\u3067\u3057\u305f")
                run(item, _talent)

            elif item == "all_missions":
                def _missions():
                    missions = sf.missions
                    names = core.core_data.get_mission_names(sf)
                    conditions = core.core_data.get_mission_conditions(sf)
                    if names.names is None or conditions.conditions is None:
                        raise ValueError("ミッションデータがありません")
                    for mission_id in list(names.names.keys()):
                        if mission_id not in missions.clear_states:
                            continue
                        cond = conditions.conditions.get(mission_id)
                        if cond is None:
                            continue
                        missions.clear_states[mission_id] = 2
                        missions.requirements[mission_id] = cond.progress_count
                run(item, _missions)

            elif item == "main_clear":
                run(item, lambda: clear_chapters(sf.story, 3))

            elif item == "zombie_clear":
                run(item, lambda: clear_chapters(sf.outbreaks))

            elif item == "old_legend_clear":
                run(item, lambda: clear_chapters(sf.event_stages, 0, 0))

            elif item == "true_legend_clear":
                run(item, lambda: clear_chapters(sf.legend_quest))

            elif item == "zero_legend_clear":
                run(item, lambda: clear_chapters(sf.zero_legends))

            elif item == "makai_clear":
                run(item, lambda: clear_chapters(sf.uncanny))

            elif item == "event_clear":
                run(item, lambda: clear_chapters(sf.event_stages, 0, 1))

            elif item == "clear_nyanko_tower":
                run(item, lambda: clear_chapters(sf.tower))

            elif item == "all_char_unlock":
                def _unlock():
                    for cat in sf.cats.get_all_cats():
                        try:
                            cat.unlock(sf)
                        except Exception:
                            pass
                run(item, _unlock)

            elif item == "error_char_delete":
                def _del_err():
                    for cat in sf.cats.get_cats_non_obtainable(sf):
                        try:
                            cat.remove(save_file=sf)
                        except Exception:
                            pass
                run(item, _del_err)

            elif item == "all_char_lv_max":
                def _lvmax():
                    up = core.Upgrade(70, 50)
                    for cat in sf.cats.get_all_cats():
                        try:
                            cat.set_upgrade(sf, up)
                        except Exception:
                            pass
                run(item, _lvmax)

            elif item == "all_char_max_form":
                def _form():
                    cats = sf.cats.get_all_cats()
                    if not cats:
                        raise ValueError("キャラデータがありません")
                    pic_book = sf.cats.read_nyanko_picture_book(sf)
                    if pic_book.cats is None:
                        raise ValueError("キャラ形態データを取得できません")
                    changed = 0
                    for cat in cats:
                        pic_book_cat = pic_book.get_cat(cat.id)
                        if pic_book_cat is None:
                            continue
                        cat.fourth_form = 0
                        cat.set_form_true(
                            sf,
                            pic_book_cat.total_forms,
                            set_current_form=True,
                            fourth_form=True,
                        )
                        changed += 1
                    if changed == 0:
                        raise ValueError("キャラ形態データが見つかりません")
                run(item, _form)

            elif item == "medal_all":
                def _medals():
                    for i in range(1, 500):
                        try:
                            sf.medals.add_medal(i)
                        except Exception:
                            pass
                run(item, _medals)

            elif item == "enemy_book_all":
                run(item, lambda: fill(sf.enemy_guide, 1))

            elif item == "user_rank_all":
                def _rank():
                    for i in range(1, 100):
                        try:
                            sf.user_rank_rewards.set_claimed(i)
                        except Exception:
                            pass
                run(item, _rank)

            elif item == "gold_pass":
                def _gold():
                    club = sf.officer_pass.gold_pass
                    club.get_gold_pass(
                        core.NyankoClub.get_random_officer_id(), 30, sf)
                run(item, _gold)

            elif item == "facility_max":
                def _facility():
                    skills = sf.special_skills.get_valid_skills()
                    for i in range(len(skills)):
                        try:
                            sf.special_skills.set_upgrade(i, core.Upgrade(10, 20))
                        except Exception:
                            pass
                run(item, _facility)

            elif item == "ad_free":
                run(item, sf.max_rank_up_sale)

            elif item == "gamatoto_max":
                run(item, lambda: setattr(sf.gamatoto, "level", 99))

            elif item == "gamatoto_legend":
                def _helpers():
                    members_name = core.core_data.get_gamatoto_members_name(sf)
                    levels = core.core_data.get_gamatoto_levels(sf)
                    max_helpers = levels.get_total_helpers()
                    rarities = members_name.get_all_rarity_names()
                    if not rarities:
                        raise ValueError("助手データがありません")
                    top = len(rarities) - 1
                    members = list(members_name.get_all_rarity(top) or [])
                    limit = max_helpers if max_helpers else len(members)
                    helpers = [Helper(m.member_id) for m in members[:limit]]
                    sf.gamatoto.helpers = Helpers(helpers)
                run(item, _helpers)

            elif item == "ototo_max":
                def _ototo():
                    if sf.ototo.cannons is None:
                        sf.ototo.cannons = Cannons.init(sf.game_version)
                    recipe = CastleRecipeUnlock(sf)
                    for cid in range(0, 12):
                        cannon = sf.ototo.get_cannon(cid)
                        if cannon is None:
                            continue
                        cannon.development = max(cannon.development, 3)
                        for part in range(len(cannon.levels)):
                            mx = recipe.get_max_level(cid, part)
                            if mx is None:
                                continue
                            cannon.levels[part] = mx
                run(item, _ototo)

            elif item == "shrine_max":
                run(item, lambda: setattr(sf.cat_shrine, "level", 99))

            elif item == "slot_max":
                run(item, lambda: setattr(sf.lineups, "unlocked_slots", 10))

            elif item == "playtime_max":
                run(item, lambda: setattr(
                    sf.officer_pass, "play_time", 2 ** 31 - 1))

            elif item == "telop_delete":
                run(item, lambda: setattr(sf.unlock_popups, "popups", {}))

            else:
                results[item] = False

        return {"success": True, "results": results}

    def generate_transfer_codes(self) -> dict:
        transfer = ''.join(random.choice('0123456789') for _ in range(9))
        pin = ''.join(random.choice('0123456789') for _ in range(4))
        return {"transfer_code": transfer, "pin": pin}
