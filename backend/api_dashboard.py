"""
AARAMBH API Dashboard — Python GUI for testing all backend endpoints
Run: python api_dashboard.py
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
import urllib.request
import urllib.error
from datetime import datetime

BASE_URL = "http://localhost:8001"

# ── All backend endpoints grouped by category ──
ENDPOINT_GROUPS = {
    "Health & Status": [
        ("GET", "/health", "Server Health"),
    ],
    "Events & Entities": [
        ("GET", "/api/v1/events/?page_size=5", "List Events"),
        ("GET", "/api/v1/entities/?page_size=5", "List Entities"),
        ("GET", "/api/v1/analytics/dashboard", "Dashboard Analytics"),
    ],
    "US Market (yfinance)": [
        ("GET", "/api/v1/market/heatmap", "Market Heatmap (56 stocks)"),
        ("GET", "/api/v1/market/quote/NVDA", "Stock Quote: NVDA"),
        ("GET", "/api/v1/market/quote/AAPL", "Stock Quote: AAPL"),
        ("GET", "/api/v1/market/profile/NVDA", "Stock Profile: NVDA"),
        ("GET", "/api/v1/market/history/NVDA?period=1M", "History: NVDA 1M"),
        ("GET", "/api/v1/market/financials/NVDA", "Financials: NVDA"),
        ("GET", "/api/v1/market/ownership/NVDA", "Ownership: NVDA"),
        ("GET", "/api/v1/market/ratings/NVDA", "Ratings: NVDA"),
        ("GET", "/api/v1/market/compare?tickers=AAPL,MSFT,GOOG", "Compare Stocks"),
        ("GET", "/api/v1/market/candles/NVDA?timeframe=1d&period=1mo", "Candles: NVDA"),
        ("GET", "/api/v1/market/indices", "Global Indices"),
        ("GET", "/api/v1/market/crypto", "Crypto Prices"),
        ("GET", "/api/v1/market/sectors", "Sector ETFs"),
        ("GET", "/api/v1/market/treasury-yields", "Treasury Yields"),
    ],
    "Indian Market (IndianAPI + FMP)": [
        ("GET", "/api/v1/indian-market/quote/RELIANCE", "Indian Quote: RELIANCE"),
        ("GET", "/api/v1/indian-market/quote/TCS", "Indian Quote: TCS"),
        ("GET", "/api/v1/indian-market/nifty50", "NIFTY 50 Heatmap"),
        ("GET", "/api/v1/indian-market/indices", "Indian Indices"),
        ("GET", "/api/v1/indian-market/ipo", "IPO Data"),
        ("GET", "/api/v1/indian-market/mutual-funds", "Mutual Funds"),
        ("GET", "/api/v1/indian-market/overview", "Combined Overview"),
        ("GET", "/api/v1/indian-market/fmp/quote/AAPL", "FMP Quote: AAPL"),
        ("GET", "/api/v1/indian-market/fmp/gainers", "FMP Top Gainers"),
        ("GET", "/api/v1/indian-market/fmp/losers", "FMP Top Losers"),
        ("GET", "/api/v1/indian-market/fmp/active", "FMP Most Active"),
        ("GET", "/api/v1/indian-market/fmp/financials/AAPL", "FMP Financials: AAPL"),
        ("GET", "/api/v1/indian-market/fmp/profile/MSFT", "FMP Profile: MSFT"),
        ("GET", "/api/v1/indian-market/fmp/economic-calendar", "FMP Econ Calendar"),
        ("GET", "/api/v1/indian-market/fmp/earnings-calendar", "FMP Earnings Calendar"),
        ("GET", "/api/v1/indian-market/fmp/screener?market_cap_min=50000000000&limit=10", "FMP Stock Screener (50B+)"),
    ],
    "Economy": [
        ("GET", "/api/v1/economy/sentiment", "Market Sentiment"),
        ("GET", "/api/v1/economy/crypto", "Crypto Overview"),
        ("GET", "/api/v1/economy/growth", "US GDP Growth"),
        ("GET", "/api/v1/economy/inflation", "US Inflation"),
        ("GET", "/api/v1/economy/employment", "Employment Data"),
        ("GET", "/api/v1/economy/rates", "Interest Rates"),
    ],
    "Investors": [
        ("GET", "/api/v1/investors/funds", "Top Institutional Funds"),
        ("GET", "/api/v1/investors/portfolios", "Portfolio Movements"),
        ("GET", "/api/v1/investors/congress", "Congress Trades"),
    ],
    "Knowledge Graph": [
        ("GET", "/api/v1/graph/stats", "Graph Stats"),
        ("GET", "/api/v1/graph/nodes?limit=10", "Graph Nodes"),
        ("GET", "/api/v1/graph/relationships?limit=10", "Graph Relationships"),
    ],
    "AI & Swarm": [
        ("GET", "/api/v1/ai/providers", "AI Providers"),
        ("GET", "/api/v1/ai/models", "AI Models"),
        ("GET", "/api/v1/swarm/status", "Swarm Status"),
        ("GET", "/api/v1/swarm/agents", "Swarm Agents"),
    ],
    "Ingestion & Debug": [
        ("GET", "/api/v1/ingest/status", "Ingestion Status"),
        ("GET", "/api/v1/ingest/scheduler", "Scheduler Status"),
        ("GET", "/api/v1/debug/info", "Debug Info"),
    ],
    "Web Scraping (Google/Social)": [
        ("GET", "/api/v1/scrape/google-finance/RELIANCE", "Google Finance Snapshot"),
        ("GET", "/api/v1/scrape/google-news?q=NIFTY&limit=5", "Google News (RSS)"),
        ("GET", "/api/v1/scrape/ai-mode?q=Current+NIFTY+Price", "Google AI Mode"),
        ("GET", "/api/v1/scrape/reddit/indiafinance", "Reddit India Finance"),
        ("GET", "/api/v1/scrape/trends?q=Stock+Market", "Google Trends"),
    ],
    "Knowledge Graph": [
        ("GET", "/api/v1/kg/dynamic?q=Indian+Banking+Sector", "Build Dynamic KG"),
        ("GET", "/api/v1/kg/snapshot", "Current KG Snapshot"),
    ],
    "System": [
        ("GET", "/api/v1/health", "Health Check"),
        ("GET", "/api/v1/debug/info", "Debug Info"),
    ],
}


class APIDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("AARAMBH API Dashboard")
        self.root.geometry("1400x900")
        self.root.configure(bg="#0d1117")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#0d1117")
        style.configure("TLabel", background="#0d1117", foreground="#e6edf3", font=("Consolas", 10))
        style.configure("TButton", background="#238636", foreground="white", font=("Segoe UI", 9, "bold"), padding=4)
        style.map("TButton", background=[("active", "#2ea043")])
        style.configure("Treeview", background="#161b22", foreground="#e6edf3", rowheight=28,
                         fieldbackground="#161b22", font=("Consolas", 9))
        style.configure("Treeview.Heading", background="#21262d", foreground="#8b949e", font=("Segoe UI", 9, "bold"))
        style.configure("TNotebook", background="#0d1117")
        style.configure("TNotebook.Tab", background="#21262d", foreground="#8b949e", padding=[12, 4],
                         font=("Segoe UI", 9))
        style.map("TNotebook.Tab", background=[("selected", "#0d1117")], foreground=[("selected", "#58a6ff")])

        # Header
        header = tk.Frame(root, bg="#161b22", height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="◆ AARAMBH API DASHBOARD", bg="#161b22", fg="#58a6ff",
                 font=("Segoe UI", 14, "bold")).pack(side="left", padx=15)
        tk.Label(header, text=f"Target: {BASE_URL}", bg="#161b22", fg="#8b949e",
                 font=("Consolas", 10)).pack(side="left", padx=15)

        self.status_label = tk.Label(header, text="● Ready", bg="#161b22", fg="#3fb950",
                                      font=("Segoe UI", 10, "bold"))
        self.status_label.pack(side="right", padx=15)

        # Main splitter
        main = tk.PanedWindow(root, orient="horizontal", bg="#0d1117", sashwidth=3, sashrelief="flat")
        main.pack(fill="both", expand=True, padx=5, pady=5)

        # Left panel — endpoint tree
        left = tk.Frame(main, bg="#0d1117", width=420)
        main.add(left, minsize=350)

        # Custom URL bar
        url_frame = tk.Frame(left, bg="#161b22")
        url_frame.pack(fill="x", pady=(0, 5))
        tk.Label(url_frame, text="URL:", bg="#161b22", fg="#8b949e", font=("Consolas", 9)).pack(side="left", padx=5)
        self.url_var = tk.StringVar(value="/health")
        self.url_entry = tk.Entry(url_frame, textvariable=self.url_var, bg="#0d1117", fg="#e6edf3",
                                   insertbackground="#58a6ff", font=("Consolas", 10), relief="flat", bd=2)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        send_btn = tk.Button(url_frame, text="▶ SEND", bg="#238636", fg="white", font=("Segoe UI", 9, "bold"),
                              relief="flat", cursor="hand2", command=self._send_custom)
        send_btn.pack(side="right", padx=5, pady=5)

        # Run all button
        runall_btn = tk.Button(left, text="⚡ RUN ALL ENDPOINTS", bg="#1f6feb", fg="white",
                                font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                                command=self._run_all)
        runall_btn.pack(fill="x", pady=(0, 5))

        # Endpoint tree
        tree_frame = tk.Frame(left, bg="#161b22")
        tree_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(tree_frame, columns=("method", "status", "time"), show="tree headings", height=30)
        self.tree.heading("method", text="Method")
        self.tree.heading("status", text="Status")
        self.tree.heading("time", text="Time")
        self.tree.column("#0", width=250, minwidth=200)
        self.tree.column("method", width=50, anchor="center")
        self.tree.column("status", width=50, anchor="center")
        self.tree.column("time", width=60, anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", self._on_tree_double_click)

        # Populate tree
        self._endpoint_map = {}
        for group, endpoints in ENDPOINT_GROUPS.items():
            gid = self.tree.insert("", "end", text=f"📁 {group}", open=True)
            for method, path, label in endpoints:
                eid = self.tree.insert(gid, "end", text=label, values=(method, "—", "—"))
                self._endpoint_map[eid] = (method, path, label)

        # Right panel — response viewer
        right = tk.Frame(main, bg="#0d1117")
        main.add(right, minsize=500)

        # Response header
        resp_header = tk.Frame(right, bg="#161b22", height=35)
        resp_header.pack(fill="x")
        resp_header.pack_propagate(False)
        self.resp_title = tk.Label(resp_header, text="Response", bg="#161b22", fg="#58a6ff",
                                    font=("Segoe UI", 11, "bold"))
        self.resp_title.pack(side="left", padx=10)
        self.resp_info = tk.Label(resp_header, text="", bg="#161b22", fg="#8b949e", font=("Consolas", 9))
        self.resp_info.pack(side="right", padx=10)

        # Response text
        self.response_text = scrolledtext.ScrolledText(
            right, bg="#0d1117", fg="#e6edf3", insertbackground="#58a6ff",
            font=("Consolas", 10), relief="flat", bd=0, wrap="word",
            selectbackground="#1f6feb", selectforeground="white"
        )
        self.response_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Results counter
        self.results_frame = tk.Frame(right, bg="#161b22", height=30)
        self.results_frame.pack(fill="x")
        self.results_frame.pack_propagate(False)
        self.results_counter = tk.Label(self.results_frame, text="0 endpoints tested", bg="#161b22",
                                         fg="#8b949e", font=("Consolas", 9))
        self.results_counter.pack(side="left", padx=10)

        self._results = {"ok": 0, "fail": 0}

    def _fetch(self, url: str) -> tuple:
        """Fetch a URL and return (status_code, response_text, elapsed_ms)"""
        full_url = BASE_URL + url if url.startswith("/") else url
        start = datetime.now()
        try:
            req = urllib.request.Request(full_url)
            req.add_header("User-Agent", "AARAMBH-Dashboard/1.0")
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read().decode("utf-8")
                elapsed = int((datetime.now() - start).total_seconds() * 1000)
                return resp.status, data, elapsed
        except urllib.error.HTTPError as e:
            elapsed = int((datetime.now() - start).total_seconds() * 1000)
            body = ""
            try:
                body = e.read().decode("utf-8")
            except Exception:
                pass
            return e.code, body, elapsed
        except Exception as e:
            elapsed = int((datetime.now() - start).total_seconds() * 1000)
            return 0, str(e), elapsed

    def _display_response(self, title: str, status: int, data: str, elapsed: int):
        """Display response in the viewer"""
        self.resp_title.config(text=title)
        color = "#3fb950" if 200 <= status < 300 else "#f85149"
        self.resp_info.config(text=f"HTTP {status} • {elapsed}ms", fg=color)

        self.response_text.delete("1.0", "end")
        try:
            parsed = json.loads(data)
            formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
            self.response_text.insert("1.0", formatted)
        except (json.JSONDecodeError, ValueError):
            self.response_text.insert("1.0", data)

    def _send_custom(self):
        url = self.url_var.get().strip()
        if not url:
            return
        self.status_label.config(text="● Fetching...", fg="#f0883e")
        self.root.update_idletasks()

        def do_fetch():
            status, data, elapsed = self._fetch(url)
            self.root.after(0, lambda: self._display_response(url, status, data, elapsed))
            self.root.after(0, lambda: self.status_label.config(
                text=f"● HTTP {status}", fg="#3fb950" if 200 <= status < 300 else "#f85149"
            ))

        threading.Thread(target=do_fetch, daemon=True).start()

    def _on_tree_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        item = sel[0]
        if item in self._endpoint_map:
            method, path, label = self._endpoint_map[item]
            self.url_var.set(path)

    def _on_tree_double_click(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        item = sel[0]
        if item in self._endpoint_map:
            method, path, label = self._endpoint_map[item]
            self.url_var.set(path)
            self._call_endpoint(item, method, path, label)

    def _call_endpoint(self, tree_id, method, path, label):
        self.status_label.config(text=f"● Calling {label}...", fg="#f0883e")
        self.root.update_idletasks()

        def do_fetch():
            status, data, elapsed = self._fetch(path)
            status_text = "✅" if 200 <= status < 300 else "❌"

            self.root.after(0, lambda: self.tree.set(tree_id, "status", status_text))
            self.root.after(0, lambda: self.tree.set(tree_id, "time", f"{elapsed}ms"))
            self.root.after(0, lambda: self._display_response(f"{label} ({path})", status, data, elapsed))

            if 200 <= status < 300:
                self._results["ok"] += 1
            else:
                self._results["fail"] += 1

            total = self._results["ok"] + self._results["fail"]
            self.root.after(0, lambda: self.results_counter.config(
                text=f"✅ {self._results['ok']} passed  ❌ {self._results['fail']} failed  ({total} total)"
            ))
            self.root.after(0, lambda: self.status_label.config(
                text=f"● {label}: HTTP {status}", fg="#3fb950" if 200 <= status < 300 else "#f85149"
            ))

        threading.Thread(target=do_fetch, daemon=True).start()

    def _run_all(self):
        """Run all endpoints sequentially"""
        self._results = {"ok": 0, "fail": 0}
        all_items = list(self._endpoint_map.items())

        def run_sequential(idx=0):
            if idx >= len(all_items):
                self.root.after(0, lambda: self.status_label.config(text="● All done!", fg="#3fb950"))
                self.root.after(0, lambda: messagebox.showinfo(
                    "Run Complete",
                    f"✅ {self._results['ok']} passed\n❌ {self._results['fail']} failed"
                ))
                return

            tree_id, (method, path, label) = all_items[idx]
            self.root.after(0, lambda: self.status_label.config(
                text=f"● [{idx+1}/{len(all_items)}] {label}...", fg="#f0883e"
            ))

            status, data, elapsed = self._fetch(path)
            status_text = "✅" if 200 <= status < 300 else "❌"

            self.root.after(0, lambda: self.tree.set(tree_id, "status", status_text))
            self.root.after(0, lambda: self.tree.set(tree_id, "time", f"{elapsed}ms"))

            if 200 <= status < 300:
                self._results["ok"] += 1
            else:
                self._results["fail"] += 1

            total = self._results["ok"] + self._results["fail"]
            self.root.after(0, lambda: self.results_counter.config(
                text=f"✅ {self._results['ok']} passed  ❌ {self._results['fail']} failed  ({total} total)"
            ))

            # Show last response
            self.root.after(0, lambda: self._display_response(f"{label} ({path})", status, data, elapsed))

            # Small delay to avoid rate limiting
            self.root.after(200, lambda: threading.Thread(target=run_sequential, args=(idx + 1,), daemon=True).start())

        threading.Thread(target=run_sequential, daemon=True).start()


def main():
    root = tk.Tk()
    app = APIDashboard(root)
    root.mainloop()


if __name__ == "__main__":
    main()
