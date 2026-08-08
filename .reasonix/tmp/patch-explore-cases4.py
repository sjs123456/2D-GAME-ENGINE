# -*- coding: utf-8 -*-
"""补丁4：tc13 精确状态对比判定"""
import io

path = ".reasonix/tmp/explore-cases-v1.py"
src = io.open(path, encoding="utf-8").read()

old13 = '''        btn.click()
        page.wait_for_timeout(1500)
        url_after = page.url
        dlg_after = visible_dialog(page) is not None
        body_after = body_excerpt(page, 200)
        r["hints"].append(f"URL变化={url_before == url_after}；弹窗出现={dlg_after}；DOM变化={body_before != body_after}")
        r["result"] = f"点击后：URL未变={url_before == url_after}、弹窗出现={dlg_after}、DOM变化={body_before != body_after}"
        if not dlg_after and url_before == url_after and body_before == body_after:
            r["verdict"] = "FAIL"
            r["hints"].insert(0, "OBS 候选确认：API 测试页「新建」按钮点击无响应")
        else:
            r["verdict"] = "PASS"'''
new13 = '''        def page_state():
            _dlgs = []
            try:
                for _i in range(page.locator(".el-dialog").count()):
                    _d = page.locator(".el-dialog").nth(_i)
                    if _d.is_visible():
                        _dlgs.append("d")
            except Exception:
                pass
            return {
                "url": page.url,
                "dialogs": _dlgs,
                "new_form": page.locator("input[placeholder='请输入用例名称']").count() > 0,
                "drawer": page.locator(".el-drawer:visible").count() > 0,
            }
        st_before = page_state()
        btn.click()
        page.wait_for_timeout(2000)
        st_after = page_state()
        changed = st_before != st_after
        r["hints"].append("状态对比=" + json.dumps({"before": st_before, "after": st_after}, ensure_ascii=False))
        r["result"] = f"点击后：弹窗出现={len(st_after['dialogs'])>0}、URL变化={st_before['url']!=st_after['url']}、状态变化={changed}"
        if changed or st_after["dialogs"] or st_after["new_form"]:
            r["verdict"] = "PASS"
        else:
            r["verdict"] = "FAIL"
            r["hints"].insert(0, "OBS 候选确认：API 测试页「新建」按钮点击无响应")'''
assert old13 in src, "tc13 锚点未找到"
src = src.replace(old13, new13)

io.open(path, "w", encoding="utf-8").write(src)
print("补丁4完成")
