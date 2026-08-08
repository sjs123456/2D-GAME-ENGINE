# -*- coding: utf-8 -*-
"""阶段一：进入注册页并分析表单结构
1. 打开登录页，点击「注册」入口
2. 分析注册表单所有字段、校验规则、提交按钮、验证码
3. 空表单直接提交，观察前端校验提示
4. 截图注册页
"""
import sys, io, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

BASE = "http://123.56.21.178:8080"
LOGIN_URL = BASE + "/login"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

OBSERVER_JS = r"""
() => {
  window.__toastTexts = [];
  if (window.__toastObs) { window.__toastObs.disconnect(); }
  const obs = new MutationObserver(muts => {
    const collect = (node) => {
      if (node.nodeType === 1) {
        const t = node.innerText || node.textContent || '';
        if (t.trim()) window.__toastTexts.push(t.trim());
      } else if (node.nodeType === 3) {
        const t = node.textContent || '';
        if (t.trim()) window.__toastTexts.push(t.trim());
      }
    };
    for (const m of muts) {
      for (const node of m.addedNodes) collect(node);
      if (m.type === 'characterData' && m.target && m.target.textContent && m.target.textContent.trim()) {
        window.__toastTexts.push(m.target.textContent.trim());
      }
    }
  });
  obs.observe(document.body, {childList: true, subtree: true, characterData: true});
  window.__toastObs = obs;
}
"""

def dump_form_info(page):
    """分析注册表单：所有 input/select/button/checkbox 及必填标记"""
    info = page.evaluate("""() => {
      const res = {url: location.href, title: document.title, inputs: [], selects: [], buttons: [], checkboxes: [], required_labels: [], form_attrs: [], captcha: null};
      document.querySelectorAll('input').forEach(inp => {
        const r = inp.getBoundingClientRect();
        res.inputs.push({
          name: inp.name || '', id: inp.id || '', type: inp.type || '',
          placeholder: inp.placeholder || '', required: inp.required || false,
          maxlength: inp.maxLength || null, autocomplete: inp.autocomplete || '',
          visible: r.width > 0 && r.height > 0 && inp.offsetParent !== null,
        });
      });
      document.querySelectorAll('select').forEach(s => {
        res.selects.push({name: s.name || '', id: s.id || '', options: [...s.options].map(o => o.text)});
      });
      document.querySelectorAll('button').forEach(b => {
        res.buttons.push({type: b.type || '', text: (b.innerText || b.textContent || '').trim().slice(0, 30), visible: b.offsetParent !== null});
      });
      document.querySelectorAll('input[type=checkbox], .el-checkbox, input[type=radio]').forEach(c => {
        res.checkboxes.push({cls: c.className || '', text: (c.innerText || c.closest('label')?.innerText || '').trim().slice(0, 40)});
      });
      document.querySelectorAll('label, .el-form-item__label, .el-checkbox__label, .el-radio__label').forEach(l => {
        const t = (l.innerText || l.textContent || '').trim();
        if (t) res.required_labels.push({text: t.slice(0, 60), cls: l.className || ''});
      });
      document.querySelectorAll('form').forEach(f => {
        res.form_attrs.push({action: f.action || '', method: f.method || '', cls: f.className || ''});
      });
      // 验证码：img/iframe 带 captcha/code 字样
      document.querySelectorAll('img, iframe, canvas, div').forEach(el => {
        const t = (el.className || '') + ' ' + (el.id || '') + ' ' + (el.alt || '') + ' ' + (el.src || '');
        if (/captcha|verify|code_img|kaptcha/i.test(t)) {
          const r = el.getBoundingClientRect();
          if (r.width > 30 && r.height > 20) res.captcha = {tag: el.tagName, cls: el.className || '', id: el.id || '', src: (el.src || '').slice(0, 100)};
        }
      });
      // el-form 的 rules / 自定义校验属性
      const formEl = document.querySelector('.el-form, form');
      if (formEl) {
        const attrs = {};
        for (const a of formEl.attributes) attrs[a.name] = a.value.slice(0, 200);
        res.form_attrs.push({el_form_attrs: JSON.stringify(attrs).slice(0, 1500)});
      }
      return res;
    }""")
    return info


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="zh-CN",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        )
        page = context.new_page()
        page.set_default_timeout(8000)
        api_resps = []
        page.on("response", lambda r: api_resps.append((r.status, r.url)) if "api/" in r.url else None)

        # 1. 打开登录页
        page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
        try:
            page.wait_for_load_state("networkidle", timeout=6000)
        except Exception:
            pass
        print("登录页标题:", page.title(), "| URL:", page.url)

        # 2. 找「注册」入口
        reg_found = None
        for sel in ["text=注册", "a:has-text('注册')", "button:has-text('注册')", ".el-tabs__item:has-text('注册')", "span:has-text('注册')"]:
            try:
                if page.locator(sel).count() > 0:
                    reg_found = sel
                    break
            except Exception:
                continue
        print("注册入口选择器:", reg_found)

        if reg_found:
            # 打印所有可见候选的文本/位置，选最明显的
            cand = page.locator(reg_found).first
            print("候选元素标签:", cand.evaluate("el => el.tagName"), "| 文本:", (cand.inner_text() or "").strip()[:40])
            page.evaluate(OBSERVER_JS)
            cand.click()
            page.wait_for_timeout(1500)
        try:
            page.wait_for_load_state("networkidle", timeout=6000)
        except Exception:
            pass

        print("点击注册后 URL:", page.url, "| 标题:", page.title())

        # 3. 分析表单
        info = dump_form_info(page)
        print(json.dumps(info, ensure_ascii=False, indent=2))
        with open(os.path.join(OUT_DIR, "register-form-info.json"), "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)

        # 4. 截图注册页（空表单提交前）
        page.screenshot(path=os.path.join(OUT_DIR, "register-page.png"), full_page=False)
        print("截图已保存: register-page.png")

        # 5. 空表单直接提交
        print("\n---- 空表单直接提交探测 ----")
        page.evaluate(OBSERVER_JS)
        # 找提交按钮：注册页上的主要提交按钮（非登录页按钮）
        submit_sel = None
        for sel in ["button.submit-btn", "button[type=submit]", "button:has-text('注册')", "button:has-text('注 册')", ".el-form button"]:
            try:
                n = page.locator(sel).count()
                if n > 0:
                    submit_sel = sel
                    break
            except Exception:
                continue
        print("提交按钮选择器:", submit_sel)
        if submit_sel:
            page.locator(submit_sel).first.click()
            page.wait_for_timeout(1500)
        # 收集提示
        toast_texts = []
        try:
            raw = page.evaluate("() => window.__toastTexts || []")
            for t in raw or []:
                t = str(t).strip()
                if t and t not in toast_texts:
                    toast_texts.append(t)
        except Exception:
            pass
        hints = []
        for sel in [".el-message", ".el-form-item__error", ".el-message-box", ".el-alert", ".error", ".toast"]:
            try:
                for i in range(min(page.locator(sel).count(), 5)):
                    try:
                        txt = page.locator(sel).nth(i).inner_text(timeout=500).strip()
                    except Exception:
                        txt = ""
                    if txt:
                        hints.append(f"[{sel}] {txt}")
            except Exception:
                pass
        print("toast 捕获:", json.dumps(toast_texts, ensure_ascii=False))
        print("DOM 提示:", json.dumps(hints, ensure_ascii=False))
        body_txt = ""
        try:
            body_txt = page.inner_text("body", timeout=3000).strip()
        except Exception:
            pass
        print("body 摘录:", repr(body_txt[:500]))
        # 空表单提交后的截图
        page.screenshot(path=os.path.join(OUT_DIR, "register-page-empty-submit.png"))
        print("空表单提交截图: register-page-empty-submit.png")
        print("API 响应:", api_resps)

        # 检查空表单提交后 URL 是否变化（是否走了注册接口）
        print("空提交后 URL:", page.url)

        context.close()
        browser.close()


if __name__ == "__main__":
    main()
