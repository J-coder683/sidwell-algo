import os
import sys
import argparse
import logging
from data import public
from data import documents as doc_module
from valuation import dcf
from lenses import buffett
from lenses import marks
from lenses import kkr
from lenses import blackstone
from lenses import apollo
from reports import render
from reports.render import SIDWELL_VERSION
from analysis import qualitative

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("sidwell.cli")


def load_dotenv():
    """
    Manually load .env file if it exists to avoid external library dependencies.
    """
    if os.path.exists(".env"):
        logger.info("Found .env file. Loading variables...")
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    # Strip spaces and optional quotes
                    key = key.strip()
                    val = val.strip().strip("'").strip('"')
                    os.environ[key] = val
                    logger.debug(f"Loaded env var: {key}")


def analyze(
    ticker: str,
    lenses_to_run: list | None = None,
    research_docs: list | None = None,
) -> dict:
    """
    Run the full Sidwell analysis pipeline for a ticker and return all results
    as a dict.

    Parameters
    ----------
    ticker : str
        Stock ticker (e.g. "ASIANPAINT.NS", "AAPL").
    lenses_to_run : list[str] | None
        Which lenses to evaluate. Defaults to all 5 when None.
        Valid values: "buffett", "marks", "kkr", "blackstone", "apollo".
    research_docs : list[{"filename": str, "bytes": bytes}] | None
        User-uploaded equity research PDFs. When supplied, DeepSeek sees only
        the latest concall + these research docs (sell-side optimism guardrails
        still apply). Defaults to None (existing behaviour unchanged).

    Returns
    -------
    dict with keys:
        financials, damodaran_data, rf_rate, dcf_results,
        qualitative_results, docs,
        buffett_results, marks_results, kkr_results, blackstone_results,
        apollo_results, report_path
        (lens results are None when that lens is not in lenses_to_run)
    """
    if lenses_to_run is None:
        lenses_to_run = ["buffett", "marks", "kkr", "blackstone", "apollo"]

    lenses_to_run = [ln.lower() for ln in lenses_to_run]

    logger.info(f"Starting Sidwell analysis pipeline for {ticker} (lenses: {lenses_to_run})")

    # Step 1: Fetch Financials and Market Pricing
    financials = public.fetch_financials(ticker)

    # Step 2: Fetch Risk-Free Rate from FRED
    rf_rate = public.fetch_risk_free_rate(ticker)

    # Step 3: Fetch Damodaran ERP and Sector Betas
    damodaran_data = public.fetch_damodaran_data(ticker, financials)

    # Fast Fail: Check if the company has any usable financial statements before invoking expensive Gemini
    if not financials.get("statements", {}).get("years_annual"):
        raise ValueError(f"Insufficient historical data to run projections for {ticker}. The company may have no usable statements on screener.")

    # Step 4: Discover documents and run qualitative analysis (graceful degrade)
    # DCF Engine now requires the Assumption Justification Pack (AJP) built from docs
    docs = doc_module.discover_documents(ticker)
    from analysis.historical_context import build_historical_context_md
    hist_ctx = build_historical_context_md(financials)

    # For US tickers: augment research_docs with the latest 10-K text (MD&A / Risk / Business).
    # India path is untouched — .NS/.BO tickers skip this branch entirely.
    research_docs = list(research_docs) if research_docs else []

    try:
        from data.public import fetch_damodaran_industry_fundamentals, format_industry_benchmark_doc
        _fund = fetch_damodaran_industry_fundamentals(ticker, financials)
        _doc = format_industry_benchmark_doc(_fund)
        if _doc:
            research_docs.append(_doc)
            logger.info(f"Industry benchmark added for {ticker}: {_fund.get('target_industry')} "
                        f"({_fund.get('geography')})")
    except Exception as e:
        logger.warning(f"Damodaran industry fundamentals unavailable for {ticker}: {e}")

    if not (ticker.endswith(".NS") or ticker.endswith(".BO")):
        try:
            from data.scrapers.edgar import fetch_edgar_filings_text
            research_docs += fetch_edgar_filings_text(ticker)
        except Exception as e:
            logger.warning(f"EDGAR filing text unavailable for {ticker}: {e}")

        try:
            from data.scrapers.edgar import fetch_edgar_8k_shareholder_letters
            research_docs += fetch_edgar_8k_shareholder_letters(ticker, n=2)
        except Exception as e:
            logger.warning(f"EDGAR 8-K text unavailable for {ticker}: {e}")

        try:
            from data.scrapers.apininjas import fetch_earnings_transcripts, fetch_earnings_calendar
            research_docs += fetch_earnings_transcripts(ticker, n=2)
        except Exception as e:
            logger.warning(f"API Ninjas transcripts unavailable for {ticker}: {e}")

        try:
            from data.scrapers.apininjas import fetch_earnings_calendar
            research_docs += fetch_earnings_calendar(ticker)
        except Exception as e:
            logger.warning(f"API Ninjas calendar unavailable for {ticker}: {e}")

    qualitative_results = qualitative.extract_qualitative(
        ticker, docs, historical_context=hist_ctx, research_docs=(research_docs or None)
    )

    # Step 5: Run DCF Valuation Engine
    dcf_results = dcf.run_dcf_valuation(financials, damodaran_data, rf_rate, qualitative_results)

    # Step 6-10: Evaluate requested lenses
    buffett_results = None
    marks_results = None
    kkr_results = None
    blackstone_results = None
    apollo_results = None

    if "buffett" in lenses_to_run:
        buffett_results = buffett.evaluate_buffett_lens(
            financials, dcf_results, qualitative_results=qualitative_results
        )

    if "marks" in lenses_to_run:
        marks_results = marks.evaluate_marks_lens(
            financials, dcf_results, qualitative_results=qualitative_results
        )

    if "kkr" in lenses_to_run:
        kkr_results = kkr.evaluate_kkr_lens(
            financials, dcf_results, qualitative_results=qualitative_results
        )

    if "blackstone" in lenses_to_run:
        blackstone_results = blackstone.evaluate_blackstone_lens(
            financials, dcf_results, qualitative_results=qualitative_results
        )

    if "apollo" in lenses_to_run:
        apollo_results = apollo.evaluate_apollo_lens(
            financials, dcf_results, qualitative_results=qualitative_results
        )

    # Step 11: Render Markdown Report and Save
    report_path = render.render_markdown_report(
        dcf_results, buffett_results if buffett_results else {},
        financials,
        qualitative_results=qualitative_results,
        marks_results=marks_results if marks_results else {},
        kkr_results=kkr_results if kkr_results else {},
        blackstone_results=blackstone_results if blackstone_results else {},
        apollo_results=apollo_results if apollo_results else {},
    )

    return {
        "ticker": ticker,
        "financials": financials,
        "damodaran_data": damodaran_data,
        "rf_rate": rf_rate,
        "dcf_results": dcf_results,
        "qualitative_results": qualitative_results,
        "docs": docs,
        "buffett_results": buffett_results,
        "marks_results": marks_results,
        "kkr_results": kkr_results,
        "blackstone_results": blackstone_results,
        "apollo_results": apollo_results,
        "report_path": report_path,
        "lenses_run": lenses_to_run,
    }


def main():
    parser = argparse.ArgumentParser(
        description=f"Sidwell — Personal Investment-Decision Engine ({SIDWELL_VERSION})"
    )
    parser.add_argument(
        "ticker",
        type=str,
        help="Stock ticker to analyze (e.g. ASIANPAINT.NS for India, AAPL for US)"
    )

    args = parser.parse_args()
    ticker = args.ticker.upper()

    logger.info(f"Starting Sidwell investment analysis pipeline for {ticker}...")

    # Load environment variables
    load_dotenv()

    try:
        results = analyze(ticker)

        financials = results["financials"]
        dcf_results = results["dcf_results"]
        buffett_results = results["buffett_results"]
        marks_results = results["marks_results"]
        kkr_results = results["kkr_results"]
        blackstone_results = results["blackstone_results"]
        apollo_results = results["apollo_results"]
        qualitative_results = results["qualitative_results"]
        docs = results["docs"]
        report_path = results["report_path"]

        # Print a short console summary
        print("\n" + "="*50)
        print(f" SIDWELL ANALYSIS COMPLETED FOR {ticker} ")
        print("="*50)
        print(f"Current Price   : {financials['current_price']:.2f}")
        if dcf_results.get("not_applicable"):
            print(f"Intrinsic Value : N/A — DCF not applicable to banks (DDM coming soon)")
            print(f"WACC            : N/A")
        else:
            print(f"Intrinsic Value : {dcf_results['intrinsic_value_per_share']:.2f}")
            print(f"WACC            : {dcf_results['wacc']*100:.2f}%")
        print(f"Buffett Score   : {buffett_results['score']}/{buffett_results.get('max_score', 14)}")
        print(f"Buffett Verdict : {buffett_results['verdict']}")
        print(f"Marks Score     : {marks_results['score']}/{marks_results.get('max_score', 14)}")
        print(f"Marks Verdict   : {marks_results['verdict']}")
        print(f"KKR Score       : {kkr_results['score']}/{kkr_results.get('max_score', 18)}")
        print(f"KKR Verdict     : {kkr_results['verdict']}")
        print(f"BX Score        : {blackstone_results['score']}/{blackstone_results.get('max_score', 14)}")
        print(f"BX Verdict      : {blackstone_results['verdict']}")
        print(f"Apollo Score    : {apollo_results['score']}/{apollo_results.get('max_score', 16)}")
        print(f"Apollo Verdict  : {apollo_results['verdict']}")
        if qualitative_results.get("status") == "available":
            docs_used = qualitative_results.get("documents_used", docs)
            print(
                f"Qualitative     : {len(docs_used)} doc(s) analyzed via "
                f"{qualitative_results.get('model')}"
            )
        else:
            print(
                f"Qualitative     : unavailable ({qualitative_results.get('reason')})"
            )
        print("="*50)
        print(f"Full report written to: {report_path}")
        print("="*50 + "\n")

    except Exception as e:
        logger.error(f"Execution failed for ticker {ticker}: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
