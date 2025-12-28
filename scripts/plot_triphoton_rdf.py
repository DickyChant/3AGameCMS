#!/usr/bin/env python3
"""
Modern RDataFrame-based plotter for triphoton analysis
Calculates all ATLAS-style variables on-the-fly with lazy evaluation
Supports multi-threading for better performance
"""
import ROOT
import os
import sys
import glob
import argparse
from datetime import datetime

# Enable multi-threading
ROOT.ROOT.EnableImplicitMT(4)
ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetPalette(ROOT.kViridis)

def setup_triphoton_variables(df):
    """
    Define all triphoton variables using RDataFrame
    This creates a lazy computation graph - nothing is computed until needed
    """
    # Filter for triphoton events
    df = df.Filter("nGoodPhoton >= 3", "Triphoton events")

    # Define weight (handle GenWeight sign for NLO MC)
    df = df.Define("weight",
                   "return (genWeight > 0 ? 1.0 : -1.0) * puWeight;")

    # Build TLorentzVectors for the three leading photons
    df = df.Define("p1", """
        ROOT::Math::PtEtaPhiMVector p;
        p.SetCoordinates(Photon_pt[0], Photon_eta[0], Photon_phi[0], 0.0);
        return p;
    """)

    df = df.Define("p2", """
        ROOT::Math::PtEtaPhiMVector p;
        p.SetCoordinates(Photon_pt[1], Photon_eta[1], Photon_phi[1], 0.0);
        return p;
    """)

    df = df.Define("p3", """
        ROOT::Math::PtEtaPhiMVector p;
        p.SetCoordinates(Photon_pt[2], Photon_eta[2], Photon_phi[2], 0.0);
        return p;
    """)

    # Triphoton system 4-vector
    df = df.Define("p123", "return p1 + p2 + p3;")

    # === INVARIANT MASSES ===
    df = df.Define("m12", "(p1 + p2).M()")
    df = df.Define("m13", "(p1 + p3).M()")
    df = df.Define("m23", "(p2 + p3).M()")
    df = df.Define("m123", "p123.M()")

    # Max and min diphoton masses
    df = df.Define("maa_max", "return std::max({m12, m13, m23});")
    df = df.Define("maa_min", "return std::min({m12, m13, m23});")

    # === ANGULAR VARIABLES ===
    # ΔR between photon pairs
    df = df.Define("dR12", "return ROOT::Math::VectorUtil::DeltaR(p1, p2);")
    df = df.Define("dR13", "return ROOT::Math::VectorUtil::DeltaR(p1, p3);")
    df = df.Define("dR23", "return ROOT::Math::VectorUtil::DeltaR(p2, p3);")

    # Δφ between photon pairs
    df = df.Define("dPhi12", "return ROOT::Math::VectorUtil::DeltaPhi(p1, p2);")
    df = df.Define("dPhi13", "return ROOT::Math::VectorUtil::DeltaPhi(p1, p3);")
    df = df.Define("dPhi23", "return ROOT::Math::VectorUtil::DeltaPhi(p2, p3);")

    # === TRIPHOTON SYSTEM KINEMATICS ===
    df = df.Define("pt_3gamma", "p123.Pt()")
    df = df.Define("eta_3gamma", "p123.Eta()")
    df = df.Define("phi_3gamma", "p123.Phi()")
    df = df.Define("rapidity_3gamma", "p123.Rapidity()")

    # === INDIVIDUAL PHOTON KINEMATICS ===
    # Define individual photon pT, eta, phi as columns for easier plotting
    df = df.Define("pt1", "Photon_pt[0]")
    df = df.Define("pt2", "Photon_pt[1]")
    df = df.Define("pt3", "Photon_pt[2]")
    df = df.Define("eta1", "Photon_eta[0]")
    df = df.Define("eta2", "Photon_eta[1]")
    df = df.Define("eta3", "Photon_eta[2]")
    df = df.Define("phi1", "Photon_phi[0]")
    df = df.Define("phi2", "Photon_phi[1]")
    df = df.Define("phi3", "Photon_phi[2]")

    # === KINEMATIC RATIOS ===
    df = df.Define("pt3_over_pt123", "pt3 / pt_3gamma")
    df = df.Define("pt3_over_pt1", "pt3 / pt1")
    df = df.Define("maa_max_over_m123", "maa_max / m123")
    df = df.Define("maa_min_over_m123", "maa_min / m123")

    # === EVENT SHAPE VARIABLES ===
    # Sphericity tensor calculation
    df = df.Define("sphericity", """
        // Build momentum matrix
        double p_tot = p1.P() + p2.P() + p3.P();
        if (p_tot < 1e-6) return -1.0;

        // Sphericity tensor components (normalized by total momentum)
        double s11 = (p1.Px()*p1.Px() + p2.Px()*p2.Px() + p3.Px()*p3.Px()) / p_tot;
        double s22 = (p1.Py()*p1.Py() + p2.Py()*p2.Py() + p3.Py()*p3.Py()) / p_tot;
        double s33 = (p1.Pz()*p1.Pz() + p2.Pz()*p2.Pz() + p3.Pz()*p3.Pz()) / p_tot;
        double s12 = (p1.Px()*p1.Py() + p2.Px()*p2.Py() + p3.Px()*p3.Py()) / p_tot;
        double s13 = (p1.Px()*p1.Pz() + p2.Px()*p2.Pz() + p3.Px()*p3.Pz()) / p_tot;
        double s23 = (p1.Py()*p1.Pz() + p2.Py()*p2.Pz() + p3.Py()*p3.Pz()) / p_tot;

        // For 3 particles, simplified calculation
        // Sphericity = 1.5 * (λ2 + λ3) where λ1 ≥ λ2 ≥ λ3 are eigenvalues
        // For triphoton, approximate as isotropy measure
        double trace = s11 + s22 + s33;
        return 1.5 * (1.0 - s33/trace);  // Simplified
    """)

    # === HELICITY ANGLE (cos θ* in triphoton rest frame) ===
    df = df.Define("cosTheta_star", """
        // Boost leading photon to triphoton rest frame
        auto boost = p123.BoostToCM();
        auto p1_star = ROOT::Math::VectorUtil::boost(p1, boost);
        // cos(θ*) = pz*/|p*|
        return p1_star.Pz() / p1_star.P();
    """)

    return df

def create_canvas(name, title, width=800, height=600):
    c = ROOT.TCanvas(name, title, width, height)
    c.SetLeftMargin(0.12)
    c.SetRightMargin(0.05)
    c.SetTopMargin(0.08)
    c.SetBottomMargin(0.12)
    return c

def style_histogram(hist, xtitle, ytitle, color=ROOT.kBlue+1):
    hist.SetLineColor(color)
    hist.SetLineWidth(2)
    hist.GetXaxis().SetTitle(xtitle)
    hist.GetYaxis().SetTitle(ytitle)
    hist.GetXaxis().SetTitleSize(0.045)
    hist.GetYaxis().SetTitleSize(0.045)
    hist.GetYaxis().SetTitleOffset(1.2)

def add_cms_label(canvas, lumi_text="", extra_text="Simulation"):
    canvas.cd()
    latex = ROOT.TLatex()
    latex.SetNDC()
    latex.SetTextFont(61)
    latex.SetTextSize(0.055)
    latex.DrawLatex(0.15, 0.92, "CMS")
    if extra_text:
        latex.SetTextFont(52)
        latex.SetTextSize(0.04)
        latex.DrawLatex(0.23, 0.92, extra_text)
    if lumi_text:
        latex.SetTextFont(42)
        latex.SetTextSize(0.04)
        latex.SetTextAlign(31)
        latex.DrawLatex(0.95, 0.92, lumi_text)

def plot_all_variables(df, output_dir, year, lumi):
    """Create all plots using RDataFrame lazy evaluation"""
    print("Creating plots with RDataFrame...")

    plots = []
    lumi_text = f"{year}, {lumi:.1f} fb^{{-1}}" if lumi > 0 else f"{year}"

    # === INVARIANT MASS PLOTS ===
    # Individual diphoton masses
    for var, nbins, xmin, xmax, title, color in [
        ("m12", 100, 0, 300, "M(#gamma_{1}#gamma_{2}) [GeV]", ROOT.kRed+1),
        ("m13", 100, 0, 300, "M(#gamma_{1}#gamma_{3}) [GeV]", ROOT.kBlue+1),
        ("m23", 100, 0, 300, "M(#gamma_{2}#gamma_{3}) [GeV]", ROOT.kGreen+2),
    ]:
        h = df.Histo1D((var, "", nbins, xmin, xmax), var, "weight")
        c = create_canvas(f"c_{var}", var)
        h.SetTitle("")
        style_histogram(h.GetPtr(), title, "Events / 3 GeV", color)
        h.Draw("HIST E")
        add_cms_label(c, lumi_text)
        plots.append((c, h, f"{var}.png"))

    # Triphoton mass
    h_m123 = df.Histo1D(("m123", "", 100, 0, 500), "m123", "weight")
    c_m123 = create_canvas("c_m123", "m123")
    h_m123.SetTitle("")
    style_histogram(h_m123.GetPtr(), "M(#gamma#gamma#gamma) [GeV]", "Events / 5 GeV", ROOT.kMagenta+2)
    h_m123.Draw("HIST E")
    c_m123.SetLogy()
    add_cms_label(c_m123, lumi_text)
    plots.append((c_m123, h_m123, "triphoton_mass.png"))

    # Max and min diphoton masses
    h_max = df.Histo1D(("maa_max", "", 100, 0, 300), "maa_max", "weight")
    c_max = create_canvas("c_maa_max", "maa_max")
    style_histogram(h_max.GetPtr(), "M_{#gamma#gamma}^{max} [GeV]", "Events / 3 GeV", ROOT.kOrange+1)
    h_max.Draw("HIST E")
    add_cms_label(c_max, lumi_text)
    plots.append((c_max, h_max, "maa_max.png"))

    h_min = df.Histo1D(("maa_min", "", 100, 0, 200), "maa_min", "weight")
    c_min = create_canvas("c_maa_min", "maa_min")
    style_histogram(h_min.GetPtr(), "M_{#gamma#gamma}^{min} [GeV]", "Events / 2 GeV", ROOT.kCyan+1)
    h_min.Draw("HIST E")
    add_cms_label(c_min, lumi_text)
    plots.append((c_min, h_min, "maa_min.png"))

    # === ANGULAR DISTRIBUTIONS ===
    for var, nbins, xmin, xmax, title in [
        ("dR12", 50, 0, 6, "#DeltaR(#gamma_{1}, #gamma_{2})"),
        ("dR13", 50, 0, 6, "#DeltaR(#gamma_{1}, #gamma_{3})"),
        ("dR23", 50, 0, 6, "#DeltaR(#gamma_{2}, #gamma_{3})"),
        ("dPhi12", 50, 0, 3.15, "#Delta#phi(#gamma_{1}, #gamma_{2})"),
        ("dPhi13", 50, 0, 3.15, "#Delta#phi(#gamma_{1}, #gamma_{3})"),
        ("dPhi23", 50, 0, 3.15, "#Delta#phi(#gamma_{2}, #gamma_{3})"),
    ]:
        h = df.Histo1D((var, "", nbins, xmin, xmax), var, "weight")
        c = create_canvas(f"c_{var}", var)
        style_histogram(h.GetPtr(), title, "Events")
        h.Draw("HIST E")
        add_cms_label(c, lumi_text)
        plots.append((c, h, f"{var}.png"))

    # === TRIPHOTON SYSTEM KINEMATICS ===
    for var, nbins, xmin, xmax, title in [
        ("pt_3gamma", 50, 0, 300, "p_{T}(#gamma#gamma#gamma) [GeV]"),
        ("eta_3gamma", 50, -5, 5, "#eta(#gamma#gamma#gamma)"),
        ("phi_3gamma", 50, -3.15, 3.15, "#phi(#gamma#gamma#gamma)"),
    ]:
        h = df.Histo1D((var, "", nbins, xmin, xmax), var, "weight")
        c = create_canvas(f"c_{var}", var)
        style_histogram(h.GetPtr(), title, "Events")
        h.Draw("HIST E")
        add_cms_label(c, lumi_text)
        plots.append((c, h, f"{var}.png"))

    # === KINEMATIC RATIOS ===
    for var, nbins, xmin, xmax, title in [
        ("pt3_over_pt123", 50, 0, 1, "p_{T}(#gamma_{3}) / p_{T}(#gamma#gamma#gamma)"),
        ("pt3_over_pt1", 50, 0, 1, "p_{T}(#gamma_{3}) / p_{T}(#gamma_{1})"),
        ("maa_max_over_m123", 50, 0, 1, "M_{#gamma#gamma}^{max} / M(#gamma#gamma#gamma)"),
        ("maa_min_over_m123", 50, 0, 0.8, "M_{#gamma#gamma}^{min} / M(#gamma#gamma#gamma)"),
    ]:
        h = df.Histo1D((var, "", nbins, xmin, xmax), var, "weight")
        c = create_canvas(f"c_{var}", var)
        style_histogram(h.GetPtr(), title, "Events")
        h.Draw("HIST E")
        add_cms_label(c, lumi_text)
        plots.append((c, h, f"{var}.png"))

    # === EVENT SHAPE ===
    h_sph = df.Histo1D(("sphericity", "", 50, 0, 1), "sphericity", "weight")
    c_sph = create_canvas("c_sphericity", "sphericity")
    style_histogram(h_sph.GetPtr(), "Sphericity", "Events", ROOT.kViolet+1)
    h_sph.Draw("HIST E")
    add_cms_label(c_sph, lumi_text)
    plots.append((c_sph, h_sph, "sphericity.png"))

    # === HELICITY ANGLE ===
    h_cos = df.Histo1D(("cosTheta_star", "", 50, -1, 1), "cosTheta_star", "weight")
    c_cos = create_canvas("c_cosTheta_star", "cosTheta_star")
    style_histogram(h_cos.GetPtr(), "cos#theta^{*}", "Events", ROOT.kTeal+1)
    h_cos.Draw("HIST E")
    add_cms_label(c_cos, lumi_text)
    plots.append((c_cos, h_cos, "cosTheta_star.png"))

    # === 2D CORRELATIONS ===
    # m12 vs m123
    h2d_1 = df.Histo2D(("h2d_m12_m123", "", 60, 0, 300, 60, 0, 500), "m12", "m123", "weight")
    c2d_1 = create_canvas("c_m12_vs_m123", "m12_vs_m123", 900, 700)
    c2d_1.SetRightMargin(0.15)
    c2d_1.SetLogz()
    h2d_1.GetXaxis().SetTitle("M(#gamma_{1}#gamma_{2}) [GeV]")
    h2d_1.GetYaxis().SetTitle("M(#gamma#gamma#gamma) [GeV]")
    h2d_1.Draw("COLZ")
    add_cms_label(c2d_1, lumi_text)
    plots.append((c2d_1, h2d_1, "m12_vs_m123_2d.png"))

    # pt3 vs m123
    h2d_2 = df.Histo2D(("h2d_pt3_m123", "", 50, 20, 150, 60, 0, 500), "pt3", "m123", "weight")
    c2d_2 = create_canvas("c_pt3_vs_m123", "pt3_vs_m123", 900, 700)
    c2d_2.SetRightMargin(0.15)
    h2d_2.GetXaxis().SetTitle("p_{T}(#gamma_{3}) [GeV]")
    h2d_2.GetYaxis().SetTitle("M(#gamma#gamma#gamma) [GeV]")
    h2d_2.Draw("COLZ")
    add_cms_label(c2d_2, lumi_text)
    plots.append((c2d_2, h2d_2, "pt3_vs_m123_2d.png"))

    print(f"Defined {len(plots)} plots, now triggering lazy evaluation...")

    # Save all plots (this triggers the actual computation)
    for canvas, hist, filename in plots:
        canvas.SaveAs(os.path.join(output_dir, filename))
        canvas.SaveAs(os.path.join(output_dir, filename.replace(".png", ".pdf")))

    print(f"Saved {len(plots)} plots")
    return plots

def create_html_index(output_dir, year, lumi, n_events, n_triphoton):
    """Create HTML index"""
    html_file = os.path.join(output_dir, "index.html")
    png_files = sorted(glob.glob(os.path.join(output_dir, "*.png")))
    if not png_files:
        return

    with open(html_file, 'w') as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Triphoton Variables (RDataFrame) - {year}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        h1 {{ color: #333; border-bottom: 2px solid #0066cc; padding-bottom: 10px; }}
        .info {{ background: white; padding: 15px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .plot-container {{ display: flex; flex-wrap: wrap; gap: 20px; }}
        .plot {{ background: white; padding: 15px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }}
        .plot img {{ max-width: 600px; height: auto; border: 1px solid #ddd; }}
        .plot-title {{ margin-top: 10px; font-weight: bold; color: #333; }}
        a {{ color: #0066cc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>Triphoton Analysis - All Variables (RDataFrame) - {year}</h1>
    <div class="info">
        <p><strong>Processing:</strong> RDataFrame with multi-threading (lazy evaluation)</p>
        <p><strong>Selection:</strong> nGoodPhoton ≥ 3 (Tight ID + pixel seed veto)</p>
        <p><strong>Total events:</strong> {n_events:,}</p>
        <p><strong>Triphoton events:</strong> {n_triphoton:,} ({100*n_triphoton/n_events:.2f}%)</p>
        <p><strong>Luminosity:</strong> {lumi:.2f} fb<sup>-1</sup></p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    <h2>ATLAS-style Variables</h2>
    <div class="plot-container">
""")
        for png_file in png_files:
            basename = os.path.basename(png_file)
            plot_name = basename.replace(".png", "").replace("_", " ").title()
            pdf_file = basename.replace(".png", ".pdf")
            f.write(f"""        <div class="plot">
            <a href="{basename}" target="_blank"><img src="{basename}" alt="{plot_name}"></a>
            <div class="plot-title">{plot_name}</div>
            <div style="margin-top: 5px; font-size: 0.9em;">
                <a href="{basename}">PNG</a> | <a href="{pdf_file}">PDF</a>
            </div>
        </div>
""")
        f.write("""    </div>
</body>
</html>
""")
    print(f"Created HTML index: {html_file}")

def main():
    parser = argparse.ArgumentParser(description="RDataFrame-based triphoton plotter")
    parser.add_argument("input", help="Input file pattern")
    parser.add_argument("-o", "--output", default=None, help="Output directory")
    parser.add_argument("--year", default="2022", help="Year label")
    parser.add_argument("--lumi", type=float, default=27.0, help="Luminosity in fb^-1")
    parser.add_argument("--max-files", type=int, default=None, help="Max files")
    args = parser.parse_args()

    # Output directory
    if args.output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"/eos/user/s/sqian/www/triphoton/{timestamp}_rdf"

    os.makedirs(args.output, exist_ok=True)

    # Get files
    if os.path.isfile(args.input):
        files = [args.input]
    elif os.path.isdir(args.input):
        files = glob.glob(os.path.join(args.input, "*.root"))
    else:
        files = glob.glob(args.input)

    if not files:
        print(f"Error: No files found")
        return 1

    if args.max_files:
        files = files[:args.max_files]

    print(f"Found {len(files)} files")
    print(f"Using {ROOT.GetThreadPoolSize()} threads for RDataFrame")

    # Create RDataFrame
    df = ROOT.RDataFrame("Events", files)
    n_total = df.Count().GetValue()
    print(f"Total events: {n_total}")

    # Setup all triphoton variables
    df = setup_triphoton_variables(df)

    # Count triphoton events
    n_triphoton = df.Count().GetValue()
    print(f"Triphoton events: {n_triphoton} ({100*n_triphoton/n_total:.2f}%)")

    if n_triphoton == 0:
        print("Error: No triphoton events!")
        return 1

    # Create all plots
    plot_all_variables(df, args.output, args.year, args.lumi)

    # Create HTML index
    create_html_index(args.output, args.year, args.lumi, n_total, n_triphoton)

    print(f"\nDone! Plots in {args.output}/")
    if "/eos/user/s/sqian/www/triphoton/" in args.output:
        print(f"View at: https://sqian.web.cern.ch/triphoton/{os.path.basename(args.output)}/")

    return 0

if __name__ == "__main__":
    sys.exit(main())
