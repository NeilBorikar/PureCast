"""Generate high-quality PDF report for PureCast Progress Report using fpdf2."""

from pathlib import Path
from fpdf import FPDF
from fpdf.enums import XPos, YPos


class PureCastReportPDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load system Arial for true unicode support
        arial_path = Path("C:/Windows/Fonts/arial.ttf")
        arial_bd = Path("C:/Windows/Fonts/arialbd.ttf")
        arial_it = Path("C:/Windows/Fonts/ariali.ttf")
        if arial_path.exists():
            self.add_font("Arial", "", str(arial_path))
            self.add_font("Arial", "B", str(arial_bd))
            self.add_font("Arial", "I", str(arial_it))
            self.font_family_name = "Arial"
        else:
            self.font_family_name = "Helvetica"

    def header(self):
        # Top branding header
        self.set_font(self.font_family_name, "B", 14)
        self.set_text_color(3, 105, 161)  # Sky blue #0369a1
        self.cell(100, 8, "PureCast", new_x=XPos.RIGHT, new_y=YPos.TOP, align="L")

        self.set_font(self.font_family_name, "B", 8)
        self.set_text_color(100, 116, 139)  # Slate #64748b
        self.cell(90, 8, "ENGINEERING & PRODUCT PROGRESS REPORT", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")

        # Sky blue separator line
        self.set_draw_color(2, 132, 199)
        self.set_line_width(0.6)
        self.line(10, 18, 200, 18)
        self.ln(5)

    def footer(self):
        self.set_y(-14)
        self.set_draw_color(226, 232, 240)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())

        self.set_font(self.font_family_name, "", 7.5)
        self.set_text_color(148, 163, 184)
        self.cell(120, 8, "PureCast Platform v1.0.0 | Competition Technical Submission", new_x=XPos.RIGHT, new_y=YPos.TOP, align="L")
        self.cell(70, 8, f"Page {self.page_no()}/{{nb}}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")

    def section_title(self, title):
        self.ln(3)
        self.set_fill_color(240, 249, 255)
        self.set_draw_color(186, 230, 253)
        self.set_line_width(0.4)
        self.rect(10, self.get_y(), 190, 8.5, style="DF")

        self.set_font(self.font_family_name, "B", 10)
        self.set_text_color(3, 105, 161)
        self.set_xy(13, self.get_y() + 1.2)
        self.cell(184, 6, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
        self.ln(2.5)

    def sub_title(self, title):
        self.set_font(self.font_family_name, "B", 9)
        self.set_text_color(15, 23, 42)
        self.cell(190, 5, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")

    def body_p(self, text):
        self.set_font(self.font_family_name, "", 8.5)
        self.set_text_color(51, 65, 85)
        self.multi_cell(190, 4.3, text)
        self.ln(1.8)

    def bullet_item(self, bold_prefix, text):
        self.set_font(self.font_family_name, "B", 8.5)
        self.set_text_color(3, 105, 161)
        self.cell(5, 4.3, "-", new_x=XPos.RIGHT, new_y=YPos.TOP, align="R")
        self.cell(self.get_string_width(bold_prefix) + 1.5, 4.3, bold_prefix, new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.set_font(self.font_family_name, "", 8.5)
        self.set_text_color(51, 65, 85)
        remaining_w = 190 - 5 - self.get_string_width(bold_prefix) - 1.5
        self.multi_cell(remaining_w, 4.3, text)
        self.ln(1)

    def callout_box(self, title, text, bg_rgb=(240, 253, 244), border_rgb=(16, 185, 129), text_rgb=(6, 95, 70)):
        self.set_fill_color(*bg_rgb)
        self.set_draw_color(*border_rgb)
        self.set_line_width(0.5)
        y = self.get_y()
        self.rect(10, y, 190, 15, style="DF")
        self.set_xy(13, y + 1.8)
        self.set_font(self.font_family_name, "B", 8.5)
        self.set_text_color(*text_rgb)
        self.cell(184, 4.2, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_x(13)
        self.set_font(self.font_family_name, "", 7.8)
        self.multi_cell(184, 3.6, text)
        self.set_y(y + 17)


def generate_pdf():
    pdf = PureCastReportPDF(format="A4", unit="mm")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)
    pdf.add_page()

    fn = pdf.font_family_name

    # Document Header Box
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(226, 232, 240)
    pdf.rect(10, pdf.get_y(), 190, 21, style="DF")

    pdf.set_xy(13, pdf.get_y() + 2)
    pdf.set_font(fn, "B", 12.5)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(115, 5.5, "PureCast Technical Milestone Report", new_x=XPos.RIGHT, new_y=YPos.TOP)

    pdf.set_font(fn, "B", 8)
    pdf.set_text_color(2, 132, 199)
    pdf.cell(69, 5.5, "STAGE: PHASE 1 / QUALIFICATION READY", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")

    pdf.set_xy(13, pdf.get_y())
    pdf.set_font(fn, "", 8)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(115, 4.2, "Target: Multi-Tenant IoT Filter-Health Forecasting Platform", new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(69, 4.2, "Date: November 2026 | Release v1.0.0", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")

    pdf.set_xy(13, pdf.get_y())
    pdf.set_font(fn, "I", 7.8)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(184, 4.2, "FastAPI Backend (:8000) - React 18 / TypeScript / Vite Frontend (:5173) - Physics-Informed ML", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # 1. Executive Summary
    pdf.section_title("1. Executive Summary")
    pdf.body_p(
        "PureCast is an industrial-grade, multi-tenant IoT telemetry and filter-health forecasting platform "
        "engineered for residential and commercial water purification networks. Traditional purifiers rely on crude "
        "countdown timers (typically 6 or 12 months) that replace cartridges regardless of whether the purifier treats "
        "80 ppm municipal water or harsh 1,200 ppm groundwater. This results in premature cartridge disposal "
        "(inflating maintenance cost and environmental plastic waste) or delayed replacement (risking membrane scaling "
        "and contaminated drinking water)."
    )
    pdf.body_p(
        "PureCast resolves this through a physics-informed prognostics kernel that ingests real-time sensor streams "
        "(inlet/outlet TDS, differential pressure across three transducers, flow rate, temperature, turbidity, and UV-C "
        "ballast current) to compute dynamic Remaining Useful Life (RUL) with confidence intervals for all five stages."
    )

    # Milestone Scorecard Table
    pdf.set_font(fn, "B", 8)
    pdf.set_fill_color(240, 249, 255)
    pdf.set_text_color(3, 105, 161)
    pdf.set_draw_color(186, 230, 253)
    pdf.cell(75, 5.5, "Engineering Deliverable", 1, new_x=XPos.RIGHT, new_y=YPos.TOP, align="L", fill=True)
    pdf.cell(35, 5.5, "Milestone Status", 1, new_x=XPos.RIGHT, new_y=YPos.TOP, align="C", fill=True)
    pdf.cell(80, 5.5, "Production Impact & Evidence", 1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L", fill=True)

    rows = [
        ("Frontend UI & Light Theme", "100% COMPLETE", "Sky-blue/white clinical aesthetic, responsive"),
        ("Backend API & Domain Pipeline", "100% OPERATIONAL", "FastAPI + Async SQLAlchemy, RFC 7807 problem details"),
        ("Consumable Stage Modeling", "5/5 STAGES", "Sediment, Carbon, Membrane Shield, RO Core, UV Lamp"),
        ("Real-Time Telemetry Stream", "ACTIVE (1.85 L/min)", "Continuous hydrodynamic sensor simulation array"),
        ("Interactive Video Simulator", "COMPLETE", "Pump toggle, 960 ppm TDS surge test, auto-dispatch"),
        ("Multi-Tenant Fleet Isolation", "VERIFIED", "Atomberg Technologies & Aquaguard OEM support"),
        ("Production Build Status", "PASSED (15.01s)", "Vite production bundle compiled with zero errors"),
    ]

    pdf.set_font(fn, "", 7.8)
    pdf.set_text_color(51, 65, 85)
    for i, (deliv, status, impact) in enumerate(rows):
        pdf.set_fill_color(255, 255, 255) if i % 2 == 0 else pdf.set_fill_color(248, 250, 252)
        pdf.cell(75, 4.8, deliv, 1, new_x=XPos.RIGHT, new_y=YPos.TOP, align="L", fill=True)
        pdf.set_font(fn, "B", 7.5)
        pdf.set_text_color(4, 120, 87)
        pdf.cell(35, 4.8, status, 1, new_x=XPos.RIGHT, new_y=YPos.TOP, align="C", fill=True)
        pdf.set_font(fn, "", 7.8)
        pdf.set_text_color(51, 65, 85)
        pdf.cell(80, 4.8, impact, 1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L", fill=True)
    pdf.ln(3)

    # 2. Architecture & Data Flow
    pdf.section_title("2. System Architecture & Data Flow")
    pdf.body_p(
        "PureCast is structured with clean decoupling across edge sensing, high-throughput cloud ingestion, "
        "prognostic computation, and responsive client monitoring:"
    )

    pdf.set_font("Courier", "B", 7.2)
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(203, 213, 225)
    pdf.rect(10, pdf.get_y(), 190, 26, style="DF")
    pdf.set_xy(12, pdf.get_y() + 1.5)
    pdf.set_text_color(15, 23, 42)
    arch_art = (
        "[IoT Purifier Sensors]        [PureCast Cloud Backend (:8000)]        [PureCast Web Client (:5173)]\n"
        " - P1, P2, P3 Transducers   --> - /api/v1/telemetry/batch Ingest     --> - 5 Radial Stage Health Rings\n"
        " - TDS In (745) / Out (38)      - HMAC-SHA256 Auth Guard                 - Hydro-Flow Schematics\n"
        " - Flow Rate (1.85 L/min)       - Physics-Informed RUL Engine            - Recharts Predictive Curves\n"
        " - UV Ballast Current (418)     - AI Anomaly & Scaling Detector          - 1-Click Technician Dispatch\n"
        " - ESP32 / Gateway Client       - SQLite / PostgreSQL Persistence        - Multi-Tenant Persona View"
    )
    pdf.multi_cell(186, 3.8, arch_art)
    pdf.set_y(pdf.get_y() + 4)

    # Page Break for Key Accomplishments
    pdf.add_page()

    # 3. Key Accomplishments
    pdf.section_title("3. Key Accomplishments & Delivered Capabilities")

    pdf.sub_title("A. Light Sky-Blue & White Clinical UI")
    pdf.body_p(
        "Crafted a high-trust, clinical visual language tailored for home appliance consumers and enterprise OEM "
        "command centers. Implemented with sky-blue gradients (#0284c7, #0ea5e9, #bae6fd), pure white glassmorphic cards, "
        "and Google's Plus Jakarta Sans typography."
    )

    pdf.sub_title("B. 5-Stage Independent Cartridge Prognostics Matrix")
    pdf.body_p(
        "Each consumable stage is evaluated and displayed with real-time radial health rings, Remaining Useful Life (RUL) "
        "days with confidence intervals, and volume utilization:"
    )
    pdf.bullet_item("1. Sediment Pre-Filter (Mechanical): ", "Traps sand/rust down to 5 um. Monitors P1-P2 delta and turbidity drift.")
    pdf.bullet_item("2. Activated Carbon Block (Adsorption): ", "Removes chlorine and VOCs based on cumulative throughput liters.")
    pdf.bullet_item("3. Membrane Protector (Anti-Scalant): ", "Chelates Ca2+/Mg2+ ions to inhibit RO scaling in hard-water zones.")
    pdf.bullet_item("4. Thin-Film RO Membrane (Hyperfiltration): ", "Core 0.0001 um filtration. 94.9% salt rejection (745 -> 38 ppm).")
    pdf.bullet_item("5. UV-C Sterilization Lamp (Germicidal): ", "Destroys pathogens with 254nm UV. Tracks 418 mA ballast current.")

    pdf.sub_title("C. Live Hydrodynamic Flow Pipeline")
    pdf.body_p(
        "Animated 6-node schematic (Inlet -> Sediment -> Carbon -> 12V DC Booster Pump -> RO Core -> UV Faucet) with live "
        "monitoring of P1 (2.85 bar), P2 (2.15 bar), P3 (0.32 bar), flow rate (1.85 L/min), and cumulative daily volume (14.2 L)."
    )

    pdf.sub_title("D. Interactive Video Simulator Triggers")
    pdf.body_p(
        "Built-in demonstration controls in the top bar allow live simulation on camera: 'Pump: RUNNING/STANDBY' toggles "
        "water flow, 'Inject TDS Spike' triggers an instant 960 ppm municipal surge with adaptive RO compensation, and "
        "'Run Diagnostic Scan' runs instant cross-sensor validation."
    )

    pdf.sub_title("E. Closed-Loop Maintenance & Supply Chain Integration")
    pdf.body_p(
        "One-click 'Priority Reorder Cartridge' action updates cartridge health to 100% and automatically assigns field technician "
        "Ramesh Patel, closing the loop between prognostics and physical service fulfillment."
    )

    pdf.sub_title("F. Multi-Tenant Fleet Management & Personas")
    pdf.body_p(
        "Complete multi-tenant isolation between Atomberg Technologies and Aquaguard OEM Services, with 1-click persona switching "
        "across Operations Admin, Field Technician, and Household Consumer (Priya Sharma)."
    )

    # 4. Technical Problems Identified & Resolved
    pdf.section_title("4. Technical Problems Identified & Resolved")

    pdf.set_font(fn, "B", 7.8)
    pdf.set_fill_color(240, 249, 255)
    pdf.set_text_color(3, 105, 161)
    pdf.cell(65, 5.2, "Problem Identified", 1, new_x=XPos.RIGHT, new_y=YPos.TOP, align="L", fill=True)
    pdf.cell(125, 5.2, "Engineering Solution & Verification", 1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L", fill=True)

    bugs = [
        ("Duplicate ORM Declarations", "Removed duplicate classes for TestRun, AuditLog, DeviceState, DeadLetter."),
        ("SQLAlchemy Attribute Collision", "Renamed InvoiceLineItem.metadata to item_metadata to avoid reserved keyword."),
        ("Missing Frontend Login/Tailwind", "Constructed Login.tsx, tailwind.config.js, and postcss.config.js."),
        ("Hard External Dependencies", "Made Redis and structlog optional with standard library fallbacks."),
        ("Missing Python Core Libraries", "Installed greenlet, aiosqlite, asyncpg, argon2-cffi, alembic, redis, structlog."),
        ("ModuleNotFoundError: purecast", "Packaged purecast in editable mode (pip install -e .) and added --app-dir src."),
        ("Vite Proxy ECONNREFUSED Noise", "Added /api/v1/health to FastAPI router and configured quiet proxy handling."),
    ]

    pdf.set_font(fn, "", 7.5)
    pdf.set_text_color(51, 65, 85)
    for i, (p, s) in enumerate(bugs):
        pdf.set_fill_color(255, 255, 255) if i % 2 == 0 else pdf.set_fill_color(248, 250, 252)
        pdf.cell(65, 4.6, p, 1, new_x=XPos.RIGHT, new_y=YPos.TOP, align="L", fill=True)
        pdf.cell(125, 4.6, s, 1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L", fill=True)
    pdf.ln(3)

    # 5. Verification & Test Evidence
    pdf.section_title("5. Verification & Test Evidence")
    pdf.body_p("Both frontend and backend compilation and resolution have been verified in production mode:")

    pdf.set_font("Courier", "", 7.2)
    pdf.set_fill_color(241, 245, 249)
    pdf.rect(10, pdf.get_y(), 190, 15, style="DF")
    pdf.set_xy(12, pdf.get_y() + 1.2)
    test_logs = (
        "[Frontend Build] vite v5.4.21 building for production... 2885 modules transformed.\n"
        "                 dist/assets/index-evu1JHxV.js (742 kB) | built in 15.01s (0 errors)\n"
        "[Backend Import] python -c \"from purecast.main import app\" -> App imported cleanly (Status: OK)"
    )
    pdf.multi_cell(186, 3.6, test_logs)
    pdf.set_y(pdf.get_y() + 3)

    # 6. Roadmap
    pdf.section_title("6. Next-Round Expansion Roadmap (Phase 2 & 3)")
    pdf.bullet_item("Cellular MQTT / CoAP Edge Pipeline: ", "Direct telemetry ingestion via AWS IoT Core / EMQX supporting Cat-M1 modems.")
    pdf.bullet_item("Edge TinyML Quantization: ", "Quantized LightGBM kernels running directly on ESP32-S3 for offline wear prediction.")
    pdf.bullet_item("Consumer Mobile PWA: ", "WebPush and WhatsApp Business API notifying homeowners 7 days prior to depletion.")
    pdf.bullet_item("ERP Auto-Replenishment: ", "Automated webhook integration with SAP / Zoho Inventory for warehouse dispatch.")

    # Callout
    pdf.callout_box(
        "Turnkey System Status: READY FOR DEMONSTRATION & ROUND QUALIFICATION",
        "Launch the unified platform using: .\\start_purecast.bat (FastAPI at :8000 and React UI at :5173). "
        "Follow the accompanying 3-minute video script to demonstrate the 5-stage health matrix and interactive flow simulation."
    )

    out_path = Path("D:/projects/PureCast/PURECAST_PROGRESS_REPORT.pdf")
    pdf.output(str(out_path))
    print(f"PDF successfully written to: {out_path.resolve()} ({out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    generate_pdf()
