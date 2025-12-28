#!/usr/bin/env python3
"""
Plotting macro for triphoton events (exactly 3 good photons)
Calculates invariant masses and creates triphoton-specific distributions
"""
import ROOT
import os
import sys
import glob
import argparse
from datetime import datetime

# Prevent ROOT from stealing command-line arguments
ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetPalette(ROOT.kViridis)

def create_canvas(name, title, width=800, height=600):
    """Create a canvas with standard settings"""
    c = ROOT.TCanvas(name, title, width, height)
    c.SetLeftMargin(0.12)
    c.SetRightMargin(0.05)
    c.SetTopMargin(0.08)
    c.SetBottomMargin(0.12)
    return c

def style_histogram(hist, title, xtitle, ytitle, color=ROOT.kBlue+1):
    """Apply standard styling to histogram"""
    hist.SetTitle(title)
    hist.GetXaxis().SetTitle(xtitle)
    hist.GetYaxis().SetTitle(ytitle)
    hist.SetLineColor(color)
    hist.SetLineWidth(2)
    hist.GetXaxis().SetTitleSize(0.045)
    hist.GetYaxis().SetTitleSize(0.045)
    hist.GetXaxis().SetLabelSize(0.04)
    hist.GetYaxis().SetLabelSize(0.04)
    hist.GetYaxis().SetTitleOffset(1.2)

def add_cms_label(canvas, lumi_text="", extra_text="Preliminary"):
    """Add CMS label to plot"""
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

def plot_triphoton_kinematics(chain, output_dir, year, is_mc, lumi):
    """Plot triphoton kinematics for events with exactly 3 photons"""
    print("Creating triphoton (3γ) kinematic plots...")

    weight_expr = "(genWeight > 0 ? 1 : -1) * puWeight" if is_mc else "1"
    selection = "nGoodPhoton >= 3"

    plots = []

    # Three photon pT distributions on same canvas
    h_pt = [ROOT.TH1F(f"h_pt_g{i+1}", "", 50, 20, 200) for i in range(3)]
    colors = [ROOT.kRed+1, ROOT.kBlue+1, ROOT.kGreen+2]
    labels = ["Leading #gamma", "Subleading #gamma", "Third #gamma"]

    for i in range(3):
        h_pt[i].Sumw2()
        chain.Draw(f"Photon_pt[{i}]>>h_pt_g{i+1}", f"{weight_expr} * ({selection})", "goff")
        style_histogram(h_pt[i], "", "Photon p_{T} [GeV]", "Events / 3.6 GeV", colors[i])

    c_pt = create_canvas("c_triphoton_pt", "triphoton_pt")
    h_pt[0].Draw("HIST E")
    for i in range(1, 3):
        h_pt[i].Draw("HIST E SAME")

    # Add legend
    leg = ROOT.TLegend(0.6, 0.65, 0.88, 0.85)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    for i in range(3):
        leg.AddEntry(h_pt[i], labels[i], "l")
    leg.Draw()
    add_cms_label(c_pt, f"{year}, {lumi:.1f} fb^{{-1}}" if lumi > 0 else f"{year}", "Simulation" if is_mc else "")
    plots.append((c_pt, h_pt, "triphoton_pt_comparison.png"))

    # Three photon eta distributions
    h_eta = [ROOT.TH1F(f"h_eta_g{i+1}", "", 50, -2.5, 2.5) for i in range(3)]
    for i in range(3):
        h_eta[i].Sumw2()
        chain.Draw(f"Photon_eta[{i}]>>h_eta_g{i+1}", f"{weight_expr} * ({selection})", "goff")
        style_histogram(h_eta[i], "", "Photon #eta", "Events", colors[i])

    c_eta = create_canvas("c_triphoton_eta", "triphoton_eta")
    h_eta[0].Draw("HIST E")
    for i in range(1, 3):
        h_eta[i].Draw("HIST E SAME")
    leg2 = leg.Clone()
    leg2.Draw()
    add_cms_label(c_eta, f"{year}, {lumi:.1f} fb^{{-1}}" if lumi > 0 else f"{year}", "Simulation" if is_mc else "")
    plots.append((c_eta, h_eta, "triphoton_eta_comparison.png"))

    # Individual photon distributions
    for i in range(3):
        # pT
        h = ROOT.TH1F(f"h_photon{i+1}_pt", "", 50, 20, 200)
        h.Sumw2()
        chain.Draw(f"Photon_pt[{i}]>>h_photon{i+1}_pt", f"{weight_expr} * ({selection})", "goff")
        c = create_canvas(f"c_photon{i+1}_pt", f"photon{i+1}_pt")
        style_histogram(h, "", f"Photon {i+1} p_{{T}} [GeV]", "Events / 3.6 GeV", colors[i])
        h.Draw("HIST E")
        add_cms_label(c, f"{year}, {lumi:.1f} fb^{{-1}}" if lumi > 0 else f"{year}", "Simulation" if is_mc else "")
        plots.append((c, h, f"photon{i+1}_pt.png"))

        # R9
        h_r9 = ROOT.TH1F(f"h_photon{i+1}_r9", "", 50, 0, 1.1)
        h_r9.Sumw2()
        chain.Draw(f"Photon_r9[{i}]>>h_photon{i+1}_r9", f"{weight_expr} * ({selection})", "goff")
        c_r9 = create_canvas(f"c_photon{i+1}_r9", f"photon{i+1}_r9")
        style_histogram(h_r9, "", f"Photon {i+1} R9", "Events", colors[i])
        h_r9.Draw("HIST E")
        add_cms_label(c_r9, f"{year}, {lumi:.1f} fb^{{-1}}" if lumi > 0 else f"{year}", "Simulation" if is_mc else "")
        plots.append((c_r9, h_r9, f"photon{i+1}_r9.png"))

    # Save all plots
    for canvas, hist, filename in plots:
        canvas.SaveAs(os.path.join(output_dir, filename))
        canvas.SaveAs(os.path.join(output_dir, filename.replace(".png", ".pdf")))

    print(f"Saved {len(plots)} triphoton kinematic plots")

def plot_invariant_masses(chain, output_dir, year, is_mc, lumi):
    """Calculate and plot invariant masses for triphoton system"""
    print("Calculating and plotting invariant masses...")

    weight_expr_base = "(genWeight > 0 ? 1 : -1) * puWeight" if is_mc else "1"

    # Create histograms
    h_m12 = ROOT.TH1F("h_m12", "", 100, 0, 300)
    h_m13 = ROOT.TH1F("h_m13", "", 100, 0, 300)
    h_m23 = ROOT.TH1F("h_m23", "", 100, 0, 300)
    h_m123 = ROOT.TH1F("h_m123", "", 100, 0, 500)

    for h in [h_m12, h_m13, h_m23, h_m123]:
        h.Sumw2()

    # Calculate masses event-by-event
    print("  Processing events...")
    n_events = 0
    for event in chain:
        if event.nGoodPhoton < 3:
            continue

        # Calculate weight
        weight = 1.0
        if is_mc:
            weight = (1.0 if event.genWeight > 0 else -1.0) * event.puWeight

        # Build TLorentzVectors
        p1 = ROOT.TLorentzVector()
        p2 = ROOT.TLorentzVector()
        p3 = ROOT.TLorentzVector()

        p1.SetPtEtaPhiM(event.Photon_pt[0], event.Photon_eta[0], event.Photon_phi[0], 0)
        p2.SetPtEtaPhiM(event.Photon_pt[1], event.Photon_eta[1], event.Photon_phi[1], 0)
        p3.SetPtEtaPhiM(event.Photon_pt[2], event.Photon_eta[2], event.Photon_phi[2], 0)

        # Fill histograms
        h_m12.Fill((p1+p2).M(), weight)
        h_m13.Fill((p1+p3).M(), weight)
        h_m23.Fill((p2+p3).M(), weight)
        h_m123.Fill((p1+p2+p3).M(), weight)

        n_events += 1
        if n_events % 10000 == 0:
            print(f"    Processed {n_events} triphoton events...")

    print(f"  Total triphoton events: {n_events}")

    plots = []

    # Plot diphoton masses comparison
    c_diphoton = create_canvas("c_diphoton_masses", "diphoton_masses", 900, 700)
    colors = [ROOT.kRed+1, ROOT.kBlue+1, ROOT.kGreen+2]

    style_histogram(h_m12, "", "M(#gamma#gamma) [GeV]", "Events / 3 GeV", colors[0])
    style_histogram(h_m13, "", "M(#gamma#gamma) [GeV]", "Events / 3 GeV", colors[1])
    style_histogram(h_m23, "", "M(#gamma#gamma) [GeV]", "Events / 3 GeV", colors[2])

    h_m12.Draw("HIST E")
    h_m13.Draw("HIST E SAME")
    h_m23.Draw("HIST E SAME")

    leg = ROOT.TLegend(0.6, 0.65, 0.88, 0.85)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.AddEntry(h_m12, "M(#gamma_{1}#gamma_{2})", "l")
    leg.AddEntry(h_m13, "M(#gamma_{1}#gamma_{3})", "l")
    leg.AddEntry(h_m23, "M(#gamma_{2}#gamma_{3})", "l")
    leg.Draw()

    add_cms_label(c_diphoton, f"{year}, {lumi:.1f} fb^{{-1}}" if lumi > 0 else f"{year}", "Simulation" if is_mc else "")
    plots.append((c_diphoton, [h_m12, h_m13, h_m23], "diphoton_masses_comparison.png"))

    # Plot triphoton mass
    c_triphoton = create_canvas("c_triphoton_mass", "triphoton_mass")
    style_histogram(h_m123, "", "M(#gamma#gamma#gamma) [GeV]", "Events / 5 GeV", ROOT.kMagenta+2)
    h_m123.Draw("HIST E")
    c_triphoton.SetLogy()
    add_cms_label(c_triphoton, f"{year}, {lumi:.1f} fb^{{-1}}" if lumi > 0 else f"{year}", "Simulation" if is_mc else "")
    plots.append((c_triphoton, h_m123, "triphoton_invariant_mass.png"))

    # 2D correlation: leading diphoton mass vs triphoton mass
    h2d_m12_m123 = ROOT.TH2F("h2d_m12_m123", "", 60, 0, 300, 60, 0, 500)

    for event in chain:
        if event.nGoodPhoton < 3:
            continue
        weight = 1.0
        if is_mc:
            weight = (1.0 if event.genWeight > 0 else -1.0) * event.puWeight

        p1 = ROOT.TLorentzVector()
        p2 = ROOT.TLorentzVector()
        p3 = ROOT.TLorentzVector()
        p1.SetPtEtaPhiM(event.Photon_pt[0], event.Photon_eta[0], event.Photon_phi[0], 0)
        p2.SetPtEtaPhiM(event.Photon_pt[1], event.Photon_eta[1], event.Photon_phi[1], 0)
        p3.SetPtEtaPhiM(event.Photon_pt[2], event.Photon_eta[2], event.Photon_phi[2], 0)

        h2d_m12_m123.Fill((p1+p2).M(), (p1+p2+p3).M(), weight)

    c_2d = create_canvas("c_m12_vs_m123", "m12_vs_m123", 900, 700)
    c_2d.SetRightMargin(0.15)
    c_2d.SetLogz()
    h2d_m12_m123.SetTitle("")
    h2d_m12_m123.GetXaxis().SetTitle("M(#gamma_{1}#gamma_{2}) [GeV]")
    h2d_m12_m123.GetYaxis().SetTitle("M(#gamma#gamma#gamma) [GeV]")
    h2d_m12_m123.Draw("COLZ")
    add_cms_label(c_2d, f"{year}, {lumi:.1f} fb^{{-1}}" if lumi > 0 else f"{year}", "Simulation" if is_mc else "")
    plots.append((c_2d, h2d_m12_m123, "m12_vs_m123_2d.png"))

    # Save all plots
    for canvas, hist, filename in plots:
        canvas.SaveAs(os.path.join(output_dir, filename))
        canvas.SaveAs(os.path.join(output_dir, filename.replace(".png", ".pdf")))

    print(f"Saved {len(plots)} invariant mass plots")

def create_html_index(output_dir, year, is_mc, lumi):
    """Create HTML index"""
    html_file = os.path.join(output_dir, "index.html")
    png_files = sorted(glob.glob(os.path.join(output_dir, "*.png")))
    if not png_files:
        return

    with open(html_file, 'w') as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Triphoton (3γ) Plots - {year}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        h1 {{ color: #333; border-bottom: 2px solid #0066cc; padding-bottom: 10px; }}
        .info {{ background-color: white; padding: 15px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .plot-container {{ display: flex; flex-wrap: wrap; gap: 20px; }}
        .plot {{ background-color: white; padding: 15px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }}
        .plot img {{ max-width: 600px; height: auto; border: 1px solid #ddd; }}
        .plot-title {{ margin-top: 10px; font-weight: bold; color: #333; }}
        a {{ color: #0066cc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>Triphoton Analysis (3γ Events) - {year}</h1>
    <div class="info">
        <p><strong>Selection:</strong> Events with exactly 3 good photons (nGoodPhoton ≥ 3)</p>
        <p><strong>Sample Type:</strong> {'Monte Carlo Simulation' if is_mc else 'Data'}</p>
        <p><strong>Year:</strong> {year}</p>
        {'<p><strong>Integrated Luminosity:</strong> ' + f'{lumi:.2f} fb<sup>-1</sup></p>' if lumi > 0 else ''}
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    <h2>Plots</h2>
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
    parser = argparse.ArgumentParser(description="Plot triphoton (3γ) event distributions")
    parser.add_argument("input", help="Input file pattern")
    parser.add_argument("-o", "--output", default=None, help="Output directory (default: EOS www with timestamp)")
    parser.add_argument("--year", default="2022", help="Year label")
    parser.add_argument("--lumi", type=float, default=0.0, help="Luminosity in fb^-1")
    parser.add_argument("--data", action="store_true", help="Data (not MC)")
    parser.add_argument("--max-files", type=int, default=None, help="Max files to process")
    args = parser.parse_args()

    # Create timestamped output
    if args.output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"/eos/user/s/sqian/www/triphoton/{timestamp}_3gamma"
        print(f"Using output: {args.output}")

    os.makedirs(args.output, exist_ok=True)

    # Get files
    if os.path.isfile(args.input):
        files = [args.input]
    elif os.path.isdir(args.input):
        files = glob.glob(os.path.join(args.input, "*.root"))
    else:
        files = glob.glob(args.input)

    if not files:
        print(f"Error: No files found for: {args.input}")
        return 1

    if args.max_files:
        files = files[:args.max_files]

    print(f"Found {len(files)} files")

    # Create chain
    chain = ROOT.TChain("Events")
    for f in files:
        chain.Add(f)

    total = chain.GetEntries()
    print(f"Total entries: {total}")

    # Count triphoton events
    n_3gamma = chain.GetEntries("nGoodPhoton >= 3")
    print(f"Events with ≥3 photons: {n_3gamma} ({100*n_3gamma/total:.1f}%)")

    if n_3gamma == 0:
        print("Error: No triphoton events found!")
        return 1

    # Create plots
    is_mc = not args.data
    plot_triphoton_kinematics(chain, args.output, args.year, is_mc, args.lumi)
    plot_invariant_masses(chain, args.output, args.year, is_mc, args.lumi)
    create_html_index(args.output, args.year, is_mc, args.lumi)

    print(f"\nDone! Plots saved to {args.output}/")
    if "/eos/user/s/sqian/www/triphoton/" in args.output:
        timestamp_dir = os.path.basename(args.output)
        print(f"View at: https://sqian.web.cern.ch/triphoton/{timestamp_dir}/")

    return 0

if __name__ == "__main__":
    sys.exit(main())
