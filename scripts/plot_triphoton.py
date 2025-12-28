#!/usr/bin/env python3
"""
Plotting macro for triphoton Skim files
Creates distributions of photons, jets, MET, and scale factors
Properly handles GenWeights for MC
"""
import ROOT
import os
import sys
import glob
import argparse
from array import array
from datetime import datetime

# Prevent ROOT from stealing command-line arguments
ROOT.PyConfig.IgnoreCommandLineOptions = True
# Batch mode (no GUI windows)
ROOT.gROOT.SetBatch(True)
# Better looking plots
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

    # CMS label
    latex = ROOT.TLatex()
    latex.SetNDC()
    latex.SetTextFont(61)
    latex.SetTextSize(0.055)
    latex.DrawLatex(0.15, 0.92, "CMS")

    # Extra text (Preliminary, Simulation, etc.)
    if extra_text:
        latex.SetTextFont(52)
        latex.SetTextSize(0.04)
        latex.DrawLatex(0.23, 0.92, extra_text)

    # Luminosity text
    if lumi_text:
        latex.SetTextFont(42)
        latex.SetTextSize(0.04)
        latex.SetTextAlign(31)  # Right-aligned
        latex.DrawLatex(0.95, 0.92, lumi_text)

def get_weight_expression(is_mc, include_sf=True):
    """
    Get the proper weight expression for MC events
    For MC: weight = sign(genWeight) * puWeight * photon_SF * ...
    For Data: weight = 1
    """
    if not is_mc:
        return "1"

    # Start with generator weight (take sign to handle NLO negative weights)
    weight = "(genWeight > 0 ? 1 : -1)"

    # Add pileup weight
    weight += " * puWeight"

    # Add photon scale factors if requested
    if include_sf:
        # Use leading photon SF (assuming tight selection)
        weight += " * Photon_CutBased_TightID_SF[0]"
        # Add second and third photon if they exist
        weight += " * (nGoodPhoton > 1 ? Photon_CutBased_TightID_SF[1] : 1)"
        weight += " * (nGoodPhoton > 2 ? Photon_CutBased_TightID_SF[2] : 1)"

    return weight

def get_total_genweight_sum(chain, is_mc):
    """
    Calculate sum of genWeights for normalization
    This is needed to properly normalize MC samples
    """
    if not is_mc:
        return chain.GetEntries()

    # Calculate sum of abs(genWeight)
    chain.Draw("abs(genWeight)>>h_genweight_temp", "", "goff")
    h_temp = ROOT.gDirectory.Get("h_genweight_temp")
    if h_temp:
        sum_genweights = h_temp.Integral()
        h_temp.Delete()
        return sum_genweights
    return chain.GetEntries()

def plot_1d_distributions(chain, output_dir, year, is_mc, lumi=1.0):
    """Create 1D distribution plots"""
    print("Creating 1D distributions...")

    # Get weight expression
    weight_expr = get_weight_expression(is_mc, include_sf=True)
    print(f"Using weight expression: {weight_expr}")

    # Calculate sum of weights for normalization
    sum_weights = get_total_genweight_sum(chain, is_mc)
    print(f"Sum of genWeights: {sum_weights}")

    plots = []

    # Photon distributions
    photon_vars = [
        ("nGoodPhoton", 10, 0, 10, "Number of good photons", "Events"),
        ("Photon_pt[0]", 50, 0, 300, "Leading photon p_{T} [GeV]", "Events / 6 GeV"),
        ("Photon_pt[1]", 50, 0, 200, "Subleading photon p_{T} [GeV]", "Events / 4 GeV"),
        ("Photon_pt[2]", 50, 0, 150, "Third photon p_{T} [GeV]", "Events / 3 GeV"),
        ("Photon_eta[0]", 50, -2.5, 2.5, "Leading photon #eta", "Events"),
        ("Photon_phi[0]", 50, -3.15, 3.15, "Leading photon #phi", "Events"),
        ("Photon_r9[0]", 50, 0, 1.2, "Leading photon R9", "Events"),
        ("Photon_sieie[0]", 50, 0, 0.03, "Leading photon #sigma_{i#etai#eta}", "Events"),
    ]

    for var, nbins, xmin, xmax, xtitle, ytitle in photon_vars:
        name = var.replace("[", "_").replace("]", "").replace("(", "").replace(")", "")
        h = ROOT.TH1F(f"h_{name}", "", nbins, xmin, xmax)
        h.Sumw2()  # Enable proper error calculation with weights

        # Apply weight and selection
        selection = f"({var} > -900)"  # Skip default values
        if "[" in var:  # Array access - check array size
            idx = var.split("[")[1].split("]")[0]
            array_name = var.split("[")[0]
            if "Photon" in var:
                selection = f"(nGoodPhoton > {idx})"
            elif "TightJet" in var:
                selection = f"(nTightJet_id > {idx})"

        draw_expr = f"{var}>>h_{name}"
        full_weight = f"{weight_expr} * ({selection})"

        chain.Draw(draw_expr, full_weight, "goff")

        if h.GetEntries() > 0:
            c = create_canvas(f"c_{name}", name)
            style_histogram(h, "", xtitle, ytitle)
            h.Draw("HIST E")  # Show error bars
            add_cms_label(c, f"{year}, {lumi:.1f} fb^{{-1}}" if lumi > 0 else f"{year}", "Simulation" if is_mc else "")
            plots.append((c, h, f"{name}.png"))

    # MET distributions
    met_vars = [
        ("met_user", 50, 0, 200, "E_{T}^{miss} [GeV]", "Events / 4 GeV"),
        ("met_phi_user", 50, -3.15, 3.15, "#phi(E_{T}^{miss})", "Events"),
    ]

    for var, nbins, xmin, xmax, xtitle, ytitle in met_vars:
        h = ROOT.TH1F(f"h_{var}", "", nbins, xmin, xmax)
        h.Sumw2()
        chain.Draw(f"{var}>>h_{var}", weight_expr, "goff")

        if h.GetEntries() > 0:
            c = create_canvas(f"c_{var}", var)
            style_histogram(h, "", xtitle, ytitle, ROOT.kRed+1)
            h.Draw("HIST E")
            add_cms_label(c, f"{year}, {lumi:.1f} fb^{{-1}}" if lumi > 0 else f"{year}", "Simulation" if is_mc else "")
            plots.append((c, h, f"{var}.png"))

    # Jet distributions
    jet_vars = [
        ("nTightJet_id", 15, 0, 15, "Number of tight jets", "Events"),
        ("TightJet_pt[0]", 50, 0, 400, "Leading jet p_{T} [GeV]", "Events / 8 GeV"),
        ("TightJet_eta[0]", 50, -5, 5, "Leading jet #eta", "Events"),
    ]

    for var, nbins, xmin, xmax, xtitle, ytitle in jet_vars:
        name = var.replace("[", "_").replace("]", "").replace("(", "").replace(")", "")
        h = ROOT.TH1F(f"h_{name}", "", nbins, xmin, xmax)
        h.Sumw2()

        selection = "1"
        if "[" in var:
            selection = "(nTightJet_id > 0)"

        chain.Draw(f"{var}>>h_{name}", f"{weight_expr} * ({selection})", "goff")

        if h.GetEntries() > 0:
            c = create_canvas(f"c_{name}", name)
            style_histogram(h, "", xtitle, ytitle, ROOT.kGreen+2)
            h.Draw("HIST E")
            add_cms_label(c, f"{year}, {lumi:.1f} fb^{{-1}}" if lumi > 0 else f"{year}", "Simulation" if is_mc else "")
            plots.append((c, h, f"{name}.png"))

    # Triphoton invariant mass
    mass_vars = [
        ("triphoton_mass", 100, 0, 500, "M(#gamma#gamma#gamma) [GeV]", "Events / 5 GeV"),
        ("Diphoton_lead_sublead_mass", 100, 0, 400, "M(#gamma_{1}#gamma_{2}) [GeV]", "Events / 4 GeV"),
    ]

    for var, nbins, xmin, xmax, xtitle, ytitle in mass_vars:
        h = ROOT.TH1F(f"h_{var}", "", nbins, xmin, xmax)
        h.Sumw2()
        chain.Draw(f"{var}>>h_{var}", f"{weight_expr} * ({var} > 0)", "goff")

        if h.GetEntries() > 0:
            c = create_canvas(f"c_{var}", var)
            style_histogram(h, "", xtitle, ytitle, ROOT.kMagenta+2)
            h.Draw("HIST E")
            c.SetLogy()  # Log scale for mass
            add_cms_label(c, f"{year}, {lumi:.1f} fb^{{-1}}" if lumi > 0 else f"{year}", "Simulation" if is_mc else "")
            plots.append((c, h, f"{var}.png"))

    # Scale factors and weights (MC only)
    if is_mc:
        sf_vars = [
            ("Photon_CutBased_MediumID_SF[0]", 50, 0.8, 1.2, "Leading photon Medium ID SF", "Events"),
            ("Photon_CutBased_TightID_SF[0]", 50, 0.8, 1.2, "Leading photon Tight ID SF", "Events"),
            ("puWeight", 50, 0, 3, "Pileup weight", "Events"),
            ("genWeight", 100, -2, 2, "Generator weight", "Events"),
        ]

        # Use unweighted for SF plots to see actual SF distributions
        for var, nbins, xmin, xmax, xtitle, ytitle in sf_vars:
            name = var.replace("[", "_").replace("]", "").replace("(", "").replace(")", "")
            h = ROOT.TH1F(f"h_{name}", "", nbins, xmin, xmax)

            selection = "1"
            if "[" in var:
                selection = "(nGoodPhoton > 0)"

            chain.Draw(f"{var}>>h_{name}", selection, "goff")

            if h.GetEntries() > 0:
                c = create_canvas(f"c_{name}", name)
                style_histogram(h, "", xtitle, ytitle, ROOT.kOrange+1)
                h.Draw("HIST")
                add_cms_label(c, f"{year}", "Simulation")
                plots.append((c, h, f"{name}.png"))

    # Save all plots
    for canvas, hist, filename in plots:
        canvas.SaveAs(os.path.join(output_dir, filename))
        canvas.SaveAs(os.path.join(output_dir, filename.replace(".png", ".pdf")))

    print(f"Saved {len(plots)} 1D plots to {output_dir}")

def create_html_index(output_dir, year, is_mc, lumi):
    """Create an HTML index file for easy web viewing"""
    html_file = os.path.join(output_dir, "index.html")

    # Get list of PNG files
    png_files = sorted(glob.glob(os.path.join(output_dir, "*.png")))
    if not png_files:
        return

    with open(html_file, 'w') as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Triphoton Plots - {year}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #0066cc;
            padding-bottom: 10px;
        }}
        .info {{
            background-color: white;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .plot-container {{
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
        }}
        .plot {{
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .plot img {{
            max-width: 600px;
            height: auto;
            border: 1px solid #ddd;
        }}
        .plot-title {{
            margin-top: 10px;
            font-weight: bold;
            color: #333;
        }}
        a {{
            color: #0066cc;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <h1>Triphoton Analysis Plots - {year}</h1>

    <div class="info">
        <p><strong>Sample Type:</strong> {'Monte Carlo Simulation' if is_mc else 'Data'}</p>
        <p><strong>Year:</strong> {year}</p>
        {'<p><strong>Integrated Luminosity:</strong> ' + f'{lumi:.2f} fb<sup>-1</sup></p>' if lumi > 0 else ''}
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Number of plots:</strong> {len(png_files)}</p>
    </div>

    <h2>Plots</h2>
    <div class="plot-container">
""")

        # Add each plot
        for png_file in png_files:
            basename = os.path.basename(png_file)
            plot_name = basename.replace(".png", "").replace("_", " ").title()
            pdf_file = basename.replace(".png", ".pdf")

            f.write(f"""        <div class="plot">
            <a href="{basename}" target="_blank">
                <img src="{basename}" alt="{plot_name}">
            </a>
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
    print(f"View at: https://sqian.web.cern.ch/triphoton/{os.path.basename(output_dir)}/")

def plot_2d_distributions(chain, output_dir, year, is_mc, lumi=1.0):
    """Create 2D distribution plots"""
    print("Creating 2D distributions...")

    weight_expr = get_weight_expression(is_mc, include_sf=True)
    plots = []

    # Photon pT vs eta
    h2d_pt_eta = ROOT.TH2F("h2d_photon_pt_eta", "", 50, -2.5, 2.5, 50, 20, 300)
    chain.Draw("Photon_pt[0]:Photon_eta[0]>>h2d_photon_pt_eta",
               f"{weight_expr} * (Photon_pt[0] > 20)", "goff")

    if h2d_pt_eta.GetEntries() > 0:
        c = create_canvas("c_photon_pt_eta", "photon_pt_eta", 900, 700)
        c.SetRightMargin(0.15)
        h2d_pt_eta.SetTitle("")
        h2d_pt_eta.GetXaxis().SetTitle("Leading photon #eta")
        h2d_pt_eta.GetYaxis().SetTitle("Leading photon p_{T} [GeV]")
        h2d_pt_eta.Draw("COLZ")
        add_cms_label(c, f"{year}, {lumi:.1f} fb^{{-1}}" if lumi > 0 else f"{year}", "Simulation" if is_mc else "")
        plots.append((c, h2d_pt_eta, "photon_pt_vs_eta.png"))

    # Photon eta vs phi
    h2d_eta_phi = ROOT.TH2F("h2d_photon_eta_phi", "", 50, -2.5, 2.5, 50, -3.15, 3.15)
    chain.Draw("Photon_phi[0]:Photon_eta[0]>>h2d_photon_eta_phi",
               f"{weight_expr} * (Photon_pt[0] > 20)", "goff")

    if h2d_eta_phi.GetEntries() > 0:
        c = create_canvas("c_photon_eta_phi", "photon_eta_phi", 900, 700)
        c.SetRightMargin(0.15)
        h2d_eta_phi.SetTitle("")
        h2d_eta_phi.GetXaxis().SetTitle("Leading photon #eta")
        h2d_eta_phi.GetYaxis().SetTitle("Leading photon #phi")
        h2d_eta_phi.Draw("COLZ")
        add_cms_label(c, f"{year}, {lumi:.1f} fb^{{-1}}" if lumi > 0 else f"{year}", "Simulation" if is_mc else "")
        plots.append((c, h2d_eta_phi, "photon_eta_vs_phi.png"))

    # Di-photon mass vs tri-photon mass
    h2d_mass = ROOT.TH2F("h2d_diphoton_triphoton_mass", "", 50, 0, 400, 50, 0, 500)
    chain.Draw("triphoton_mass:Diphoton_lead_sublead_mass>>h2d_diphoton_triphoton_mass",
               f"{weight_expr} * (triphoton_mass > 0 && Diphoton_lead_sublead_mass > 0)", "goff")

    if h2d_mass.GetEntries() > 0:
        c = create_canvas("c_diphoton_triphoton_mass", "mass_correlation", 900, 700)
        c.SetRightMargin(0.15)
        c.SetLogz()
        h2d_mass.SetTitle("")
        h2d_mass.GetXaxis().SetTitle("M(#gamma_{1}#gamma_{2}) [GeV]")
        h2d_mass.GetYaxis().SetTitle("M(#gamma#gamma#gamma) [GeV]")
        h2d_mass.Draw("COLZ")
        add_cms_label(c, f"{year}, {lumi:.1f} fb^{{-1}}" if lumi > 0 else f"{year}", "Simulation" if is_mc else "")
        plots.append((c, h2d_mass, "diphoton_vs_triphoton_mass.png"))

    # Save all plots
    for canvas, hist, filename in plots:
        canvas.SaveAs(os.path.join(output_dir, filename))
        canvas.SaveAs(os.path.join(output_dir, filename.replace(".png", ".pdf")))

    print(f"Saved {len(plots)} 2D plots to {output_dir}")

def main():
    parser = argparse.ArgumentParser(description="Plot distributions from triphoton Skim files")
    parser.add_argument("input", help="Input file pattern (e.g., 'test_2022_signal/*.root' or single file)")
    parser.add_argument("-o", "--output", default=None, help="Output directory for plots (default: /eos/user/s/sqian/www/triphoton/TIMESTAMP)")
    parser.add_argument("--year", default="2022", help="Year label for plots")
    parser.add_argument("--lumi", type=float, default=0.0, help="Integrated luminosity in fb^-1 (for label)")
    parser.add_argument("--data", action="store_true", help="Input is data (not MC)")
    parser.add_argument("--max-files", type=int, default=None, help="Maximum number of files to process")
    parser.add_argument("--no-html", action="store_true", help="Don't create HTML index file")
    args = parser.parse_args()

    # Create output directory with timestamp if not specified
    if args.output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"/eos/user/s/sqian/www/triphoton/{timestamp}"
        print(f"Using timestamped output directory: {args.output}")

    os.makedirs(args.output, exist_ok=True)

    # Get input files
    if os.path.isfile(args.input):
        files = [args.input]
    elif os.path.isdir(args.input):
        files = glob.glob(os.path.join(args.input, "*.root"))
    else:
        files = glob.glob(args.input)

    if not files:
        print(f"Error: No input files found for pattern: {args.input}")
        return 1

    if args.max_files:
        files = files[:args.max_files]

    print(f"Found {len(files)} input files")

    # Create TChain
    chain = ROOT.TChain("Events")
    for f in files:
        chain.Add(f)

    total_entries = chain.GetEntries()
    print(f"Total entries: {total_entries}")

    if total_entries == 0:
        print("Error: No entries found in input files")
        return 1

    # Create plots
    is_mc = not args.data
    plot_1d_distributions(chain, args.output, args.year, is_mc, args.lumi)
    plot_2d_distributions(chain, args.output, args.year, is_mc, args.lumi)

    # Create HTML index for web viewing
    if not args.no_html:
        create_html_index(args.output, args.year, is_mc, args.lumi)

    print(f"\nDone! Plots saved to {args.output}/")

    # Check if output is on EOS www area
    if "/eos/user/s/sqian/www/triphoton/" in args.output:
        timestamp_dir = os.path.basename(args.output)
        print(f"View plots at: https://sqian.web.cern.ch/triphoton/{timestamp_dir}/")
    else:
        print(f"To view locally: open {args.output}/index.html")

    return 0

if __name__ == "__main__":
    sys.exit(main())
