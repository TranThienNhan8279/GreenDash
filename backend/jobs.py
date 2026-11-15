"""Việc chạy định kỳ (APScheduler)."""
import logging
import os

import db
import rules

log = logging.getLogger("greendash.jobs")


def chay_gio():
    giay = int(os.environ.get("GREENDASH_CHU_KY_GIAY", "60"))
    a = db.call_proc("EXEC dbo.usp_QuyDoiCarbon @GiayMoiDiem = ?", (giay,))
    b = db.call_proc("EXEC dbo.usp_GhiNhanCanhBao")
    log.info("QuyDoi=%s CanhBao=%s", a, b)
    return {"quyDoi": a, "canhBao": b}


def chay_ngay():
    n = rules.de_xuat_hanh_dong()
    log.info("De xuat moi: %s", n)
    return {"deXuatMoi": n}
