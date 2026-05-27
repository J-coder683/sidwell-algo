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
        # Step 1: Fetch Financials and Market Pricing
        financials = public.fetch_financials(ticker)

        # Step 2: Fetch Risk-Free Rate from FRED
        rf_rate = public.fetch_risk_free_rate(ticker)

        # Step 3: Fetch Damodaran ERP and Sector Betas
        damodaran_data = public.fetch_damodaran_data(ticker)

        # Step 4: Run DCF Valuation Engine
        dcf_results = dcf.run_dcf_valuation(financials, damodaran_data, rf_rate)

        # Step 5: Discover documents and run qualitative analysis (graceful degrade)
        docs = doc_module.discover_documents(ticker)
        qualitative_results = qualitative.extract_qualitative(ticker, docs)

        # Step 6: Evaluate Buffett Investor Lens (14 checks)
        buffett_results = buffett.evaluate_buffett_lens(
            financials, dcf_results, qualitative_results=qualitative_results
        )

        # Step 7: Evaluate Marks Investor Lens (14 checks)
        marks_results = marks.evaluate_marks_lens(
            financials, dcf_results, qualitative_results=qualitative_results
        )

        # Step 8: Evaluate KKR Investor Lens (18 checks)
        kkr_results = kkr.evaluate_kkr_lens(
            financials, dcf_results, qualitative_results=qualitative_results
        )

        # Step 9: Evaluate Blackstone Investor Lens (14 checks)
        blackstone_results = blackstone.evaluate_blackstone_lens(
            financials, dcf_results, qualitative_results=qualitative_results
        )

        # Step 10: Evaluate Apollo Investor Lens (16 checks)
        apollo_results = apollo.evaluate_apollo_lens(
            financials, dcf_results, qualitative_results=qualitative_results
        )

        # Step 11: Render Markdown Report and Save
        report_path = render.render_markdown_report(
            dcf_results, buffett_results, financials,
            qualitative_results=qualitative_results,
            marks_results=marks_results,
            kkr_results=kkr_results,
            blackstone_results=blackstone_results,
            apollo_results=apollo_results,
        )

        # Print a short console summary
        print("\n" + "="*50)
        print(f" SIDWELL ANALYSIS COMPLETED FOR {ticker} ")
        print("="*50)
        print(f"Current Price   : {financials['current_price']:.2f}")
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
            print(
                f"Qualitative     : {len(docs)} doc(s) analyzed via "
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
