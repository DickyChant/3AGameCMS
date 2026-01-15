#!/usr/bin/env python3
"""
Plotting macro for triphoton Skim files
Creates distributions of photons, jets, MET, and scale factors
Properly handles GenWeights for MC
Uses cmsstyle for CMS-compliant plots
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

# Import and use cmsstyle for CMS-compliant plots (required)
try:
    import cmsstyle
    # Get CMS object from cmsstyle
    if hasattr(cmsstyle, 'CMS'):
        CMS = cmsstyle.CMS
    elif hasattr(cmsstyle, 'cms'):
        CMS = cmsstyle.cms
    else:
        CMS = cmsstyle
    
    # Initialize CMS style
    if hasattr(CMS, 'SetExtraText'):
        CMS.SetExtraText("Simulation Preliminary")
    if hasattr(CMS, 'SetLumi'):
        CMS.SetLumi("")  # Will be updated per plot
    
    ROOT.gStyle.SetOptStat(0)
    if hasattr(ROOT.gStyle, 'SetPalette'):
        ROOT.gStyle.SetPalette(ROOT.kViridis)
    
    print("✓ Using cmsstyle for CMS-compliant plots")
    USE_CMSSTYLE = True
except ImportError:
    print("❌ ERROR: cmsstyle is required but not available!")
    print("  Please install with: scram-venv && pip install cmsstyle")
    print("  Or run: source setup.sh")
    sys.exit(1)
except Exception as e:
    print(f"❌ ERROR: cmsstyle initialization failed: {e}")
    print("  Please check your cmsstyle installation")
    sys.exit(1)

def create_canvas(name, title, width=800, height=600):
    """Create a canvas using cmsstyle.cmsCanvas (required)"""
    # Use cmsstyle canvas
    canv = CMS.cmsCanvas('', 0, 1, 0, 1, '', '', square=CMS.kSquare, extraSpace=0.01, iPos=0)
    canv.SetName(name)
    canv.SetTitle(title)
    canv.SetCanvasSize(width, height)
    return canv

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

def add_cms_label(canvas, lumi_text="", extra_text="Simulation Preliminary", trigger_text=""):
    """Add CMS label using cmsstyle CMS object (required)"""
    canvas.cd()
    
    # Extract luminosity value from lumi_text if present
    lumi_str = ""
    if lumi_text and "fb" in lumi_text:
        try:
            import re
            match = re.search(r'(\d+\.?\d*)\s*fb', lumi_text)
            if match:
                lumi_str = f"{match.group(1)} fb^{{-1}}"
        except:
            pass
    
    # Set CMS labels using proper API
    if hasattr(CMS, 'SetExtraText'):
        CMS.SetExtraText(extra_text if extra_text else "Simulation Preliminary")
    if hasattr(CMS, 'SetLumi'):
        CMS.SetLumi(lumi_str)
    
    # The CMS label should already be drawn by cmsCanvas
    # cmsCanvas automatically draws the CMS label
    
    # Add trigger text (bottom left) if provided
    if trigger_text:
        latex = ROOT.TLatex()
        latex.SetNDC()
        latex.SetTextFont(42)
        latex.SetTextSize(0.035)
        latex.SetTextAlign(11)  # Left-aligned
        latex.DrawLatex(0.15, 0.15, trigger_text)

def auto_scale_histograms(histograms, pad_factor=1.2, log_scale=False):
    """
    Auto-scale y-axis for multiple overlaid histograms
    
    Args:
        histograms: List of TH1F histograms to scale
        pad_factor: Factor to multiply max by for padding (default 1.2 = 20% padding)
        log_scale: If True, also set minimum for log scale
    """
    if not histograms:
        return
    
    # Find maximum across all histograms
    max_val = 0.0
    min_val = float('inf')
    
    for h in histograms:
        if h and h.GetEntries() > 0:
            h_max = h.GetMaximum()
            h_min = h.GetMinimum()
            if h_max > max_val:
                max_val = h_max
            if h_min < min_val and h_min > 0:  # Only consider positive values for log
                min_val = h_min
    
    if max_val > 0:
        # Set maximum with padding
        for h in histograms:
            if h and h.GetEntries() > 0:
                h.SetMaximum(max_val * pad_factor)
        
        # For log scale, set minimum
        if log_scale and min_val < float('inf') and min_val > 0:
            # Set minimum to be a factor below the maximum
            log_min = max_val * pad_factor * 0.001  # 0.1% of max
            if min_val < log_min:
                log_min = min_val * 0.1  # 10% of actual minimum
            for h in histograms:
                if h and h.GetEntries() > 0:
                    h.SetMinimum(log_min)

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

def normalize_trigger_name(trigger_name):
    """
    Normalize trigger name by removing _v suffix if present.
    The branches in ROOT files are stored without _v suffix.
    """
    if trigger_name and trigger_name.endswith("_v"):
        return trigger_name[:-2]  # Remove "_v" suffix
    return trigger_name

def get_trigger_selection(trigger_type="none", triple_photon_trigger1=None, triple_photon_trigger2=None):
    """
    Build trigger selection string
    
    Args:
        trigger_type: "none", "triple1", "triple2", "triple_or", "diphoton"
        triple_photon_trigger1: First triple photon trigger name (e.g., "HLT_TriplePhoton_30_30_10_CaloIdLV2" or "HLT_TriplePhoton_30_30_10_CaloIdLV2_v")
        triple_photon_trigger2: Second triple photon trigger name (e.g., "HLT_TriplePhoton_30_30_10_CaloIdLV2_R9IdVL" or "HLT_TriplePhoton_30_30_10_CaloIdLV2_R9IdVL_v")
    """
    # Normalize trigger names (remove _v suffix if present)
    triple_photon_trigger1 = normalize_trigger_name(triple_photon_trigger1)
    triple_photon_trigger2 = normalize_trigger_name(triple_photon_trigger2)
    
    if trigger_type == "none":
        return "1"  # No trigger requirement
    
    if trigger_type == "triple1":
        if triple_photon_trigger1:
            return f"({triple_photon_trigger1} == 1)"
        else:
            return "1"
    
    if trigger_type == "triple2":
        if triple_photon_trigger2:
            return f"({triple_photon_trigger2} == 1)"
        else:
            return "1"
    
    if trigger_type == "triple_or":
        # OR of the two triple photon triggers
        if triple_photon_trigger1 and triple_photon_trigger2:
            return f"(({triple_photon_trigger1} == 1) || ({triple_photon_trigger2} == 1))"
        elif triple_photon_trigger1:
            return f"({triple_photon_trigger1} == 1)"
        elif triple_photon_trigger2:
            return f"({triple_photon_trigger2} == 1)"
        else:
            # Fallback to any triple photon trigger
            return "(HLT_passAnyTriplePhoton == 1)"
    
    if trigger_type == "diphoton":
        # Diphoton triggers, but exclude events where triple photon triggers fired
        return "(HLT_passAnyDiphoton == 1 && HLT_passAnyTriplePhoton == 0)"
    
    return "1"

def plot_1d_distributions(chain, output_dir, year, is_mc, lumi=1.0, 
                          triple_photon_trigger1=None, triple_photon_trigger2=None, no_trigger=False):
    """Create 1D distribution plots with overlaid trigger selections"""
    if no_trigger:
        print("Creating 1D distributions (no trigger selection)...")
        trigger_text = "No Trigger"
        trigger_selection_or = "1"
        trigger_selection_1 = "1"
        trigger_selection_2 = "1"
        trig1_display = "All Events"
        trig2_display = "All Events"
    else:
        print("Creating 1D distributions with trigger overlays...")
        
        # Normalize trigger names
        trig1_display = normalize_trigger_name(triple_photon_trigger1) if triple_photon_trigger1 else None
        trig2_display = normalize_trigger_name(triple_photon_trigger2) if triple_photon_trigger2 else None
        
        # Build trigger text for plots
        if trig1_display and trig2_display:
            trigger_text = f"Triggers: {trig1_display} || {trig2_display}"
        else:
            trigger_text = "Triple Photon Triggers"

        # Get trigger selections for all three cases
        trigger_selection_or = get_trigger_selection("triple_or", triple_photon_trigger1, triple_photon_trigger2)
        trigger_selection_1 = get_trigger_selection("triple1", triple_photon_trigger1, triple_photon_trigger2)
        trigger_selection_2 = get_trigger_selection("triple2", triple_photon_trigger1, triple_photon_trigger2)
        
        print(f"Trigger OR selection: {trigger_selection_or}")
        print(f"Trigger 1 selection: {trigger_selection_1}")
        print(f"Trigger 2 selection: {trigger_selection_2}")

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
        
        # Create three histograms for overlay
        h_or = ROOT.TH1F(f"h_{name}_or", "", nbins, xmin, xmax)
        h_1 = ROOT.TH1F(f"h_{name}_1", "", nbins, xmin, xmax)
        h_2 = ROOT.TH1F(f"h_{name}_2", "", nbins, xmin, xmax)
        
        for h in [h_or, h_1, h_2]:
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

        # Fill three histograms with different trigger selections
        combined_selection_or = f"({selection}) && ({trigger_selection_or})"
        combined_selection_1 = f"({selection}) && ({trigger_selection_1})"
        combined_selection_2 = f"({selection}) && ({trigger_selection_2})"
        
        chain.Draw(f"{var}>>h_{name}_or", f"{weight_expr} * ({combined_selection_or})", "goff")
        chain.Draw(f"{var}>>h_{name}_1", f"{weight_expr} * ({combined_selection_1})", "goff")
        chain.Draw(f"{var}>>h_{name}_2", f"{weight_expr} * ({combined_selection_2})", "goff")

        # Only create plot if at least one histogram has entries
        if h_or.GetEntries() > 0 or h_1.GetEntries() > 0 or h_2.GetEntries() > 0:
            c = create_canvas(f"c_{name}", name)
            
            # Style and draw histograms
            style_histogram(h_or, "", xtitle, ytitle, ROOT.kBlack)
            style_histogram(h_1, "", xtitle, ytitle, ROOT.kRed+1)
            style_histogram(h_2, "", xtitle, ytitle, ROOT.kBlue+1)
            
            # Draw with different line styles
            h_or.SetLineStyle(1)
            h_1.SetLineStyle(2)
            h_2.SetLineStyle(3)
            
            # Auto-scale y-axis for all histograms
            hist_list = [h_or]
            if h_1.GetEntries() > 0:
                hist_list.append(h_1)
            if h_2.GetEntries() > 0:
                hist_list.append(h_2)
            auto_scale_histograms(hist_list, pad_factor=1.2, log_scale=False)
            
            # Draw all histograms
            h_or.Draw("HIST E")
            if h_1.GetEntries() > 0:
                h_1.Draw("HIST E SAME")
            if h_2.GetEntries() > 0:
                h_2.Draw("HIST E SAME")
            
            # Add legend (larger size)
            leg = ROOT.TLegend(0.60, 0.60, 0.92, 0.92)
            leg.SetBorderSize(0)
            leg.SetFillStyle(0)
            leg.SetTextSize(0.045)  # Larger text size
            leg.SetTextFont(42)
            if not no_trigger:
                if h_or.GetEntries() > 0:
                    leg.AddEntry(h_or, f"{trig1_display} || {trig2_display}", "l")
                if h_1.GetEntries() > 0:
                    leg.AddEntry(h_1, trig1_display or "Trigger 1", "l")
                if h_2.GetEntries() > 0:
                    leg.AddEntry(h_2, trig2_display or "Trigger 2", "l")
            else:
                # For no-trigger case, all three are the same, just show one
                if h_or.GetEntries() > 0:
                    leg.AddEntry(h_or, "All Events", "l")
            leg.Draw()
            
            add_cms_label(c, f"{year}, {lumi:.1f} fb^{{-1}}" if lumi > 0 else f"{year}", 
                         "Simulation" if is_mc else "", trigger_text)
            plots.append((c, [h_or, h_1, h_2], f"{name}.png"))

    # MET distributions
    met_vars = [
        ("met_user", 50, 0, 200, "E_{T}^{miss} [GeV]", "Events / 4 GeV"),
        ("met_phi_user", 50, -3.15, 3.15, "#phi(E_{T}^{miss})", "Events"),
    ]

    for var, nbins, xmin, xmax, xtitle, ytitle in met_vars:
        # Create three histograms for overlay
        h_or = ROOT.TH1F(f"h_{var}_or", "", nbins, xmin, xmax)
        h_1 = ROOT.TH1F(f"h_{var}_1", "", nbins, xmin, xmax)
        h_2 = ROOT.TH1F(f"h_{var}_2", "", nbins, xmin, xmax)
        
        for h in [h_or, h_1, h_2]:
            h.Sumw2()
        
        chain.Draw(f"{var}>>h_{var}_or", f"{weight_expr} * ({trigger_selection_or})", "goff")
        chain.Draw(f"{var}>>h_{var}_1", f"{weight_expr} * ({trigger_selection_1})", "goff")
        chain.Draw(f"{var}>>h_{var}_2", f"{weight_expr} * ({trigger_selection_2})", "goff")

        if h_or.GetEntries() > 0 or h_1.GetEntries() > 0 or h_2.GetEntries() > 0:
            c = create_canvas(f"c_{var}", var)
            
            style_histogram(h_or, "", xtitle, ytitle, ROOT.kBlack)
            style_histogram(h_1, "", xtitle, ytitle, ROOT.kRed+1)
            style_histogram(h_2, "", xtitle, ytitle, ROOT.kBlue+1)
            
            h_or.SetLineStyle(1)
            h_1.SetLineStyle(2)
            h_2.SetLineStyle(3)
            
            # Auto-scale y-axis for all histograms
            hist_list = [h_or]
            if h_1.GetEntries() > 0:
                hist_list.append(h_1)
            if h_2.GetEntries() > 0:
                hist_list.append(h_2)
            auto_scale_histograms(hist_list, pad_factor=1.2, log_scale=False)
            
            h_or.Draw("HIST E")
            if h_1.GetEntries() > 0:
                h_1.Draw("HIST E SAME")
            if h_2.GetEntries() > 0:
                h_2.Draw("HIST E SAME")
            
            leg = ROOT.TLegend(0.60, 0.60, 0.92, 0.92)
            leg.SetBorderSize(0)
            leg.SetFillStyle(0)
            leg.SetTextSize(0.045)  # Larger text size
            leg.SetTextFont(42)
            if h_or.GetEntries() > 0:
                leg.AddEntry(h_or, f"{trig1_display} || {trig2_display}", "l")
            if h_1.GetEntries() > 0:
                leg.AddEntry(h_1, trig1_display or "Trigger 1", "l")
            if h_2.GetEntries() > 0:
                leg.AddEntry(h_2, trig2_display or "Trigger 2", "l")
            leg.Draw()
            
            add_cms_label(c, f"{year}, {lumi:.1f} fb^{{-1}}" if lumi > 0 else f"{year}", 
                         "Simulation" if is_mc else "", trigger_text)
            plots.append((c, [h_or, h_1, h_2], f"{var}.png"))

    # Jet distributions
    jet_vars = [
        ("nTightJet", 15, 0, 15, "Number of tight jets", "Events"),
        ("TightJet_pt[0]", 50, 0, 400, "Leading jet p_{T} [GeV]", "Events / 8 GeV"),
        ("TightJet_eta[0]", 50, -5, 5, "Leading jet #eta", "Events"),
    ]

    for var, nbins, xmin, xmax, xtitle, ytitle in jet_vars:
        name = var.replace("[", "_").replace("]", "").replace("(", "").replace(")", "")
        
        # Create three histograms for overlay
        h_or = ROOT.TH1F(f"h_{name}_or", "", nbins, xmin, xmax)
        h_1 = ROOT.TH1F(f"h_{name}_1", "", nbins, xmin, xmax)
        h_2 = ROOT.TH1F(f"h_{name}_2", "", nbins, xmin, xmax)
        
        for h in [h_or, h_1, h_2]:
            h.Sumw2()

        selection = "1"
        if "[" in var:
            selection = "(nTightJet > 0)"

        combined_selection_or = f"({selection}) && ({trigger_selection_or})"
        combined_selection_1 = f"({selection}) && ({trigger_selection_1})"
        combined_selection_2 = f"({selection}) && ({trigger_selection_2})"
        
        chain.Draw(f"{var}>>h_{name}_or", f"{weight_expr} * ({combined_selection_or})", "goff")
        chain.Draw(f"{var}>>h_{name}_1", f"{weight_expr} * ({combined_selection_1})", "goff")
        chain.Draw(f"{var}>>h_{name}_2", f"{weight_expr} * ({combined_selection_2})", "goff")

        if h_or.GetEntries() > 0 or h_1.GetEntries() > 0 or h_2.GetEntries() > 0:
            c = create_canvas(f"c_{name}", name)
            
            style_histogram(h_or, "", xtitle, ytitle, ROOT.kBlack)
            style_histogram(h_1, "", xtitle, ytitle, ROOT.kRed+1)
            style_histogram(h_2, "", xtitle, ytitle, ROOT.kBlue+1)
            
            h_or.SetLineStyle(1)
            h_1.SetLineStyle(2)
            h_2.SetLineStyle(3)
            
            # Auto-scale y-axis for all histograms
            hist_list = [h_or]
            if h_1.GetEntries() > 0:
                hist_list.append(h_1)
            if h_2.GetEntries() > 0:
                hist_list.append(h_2)
            auto_scale_histograms(hist_list, pad_factor=1.2, log_scale=False)
            
            h_or.Draw("HIST E")
            if h_1.GetEntries() > 0:
                h_1.Draw("HIST E SAME")
            if h_2.GetEntries() > 0:
                h_2.Draw("HIST E SAME")
            
            leg = ROOT.TLegend(0.60, 0.60, 0.92, 0.92)
            leg.SetBorderSize(0)
            leg.SetFillStyle(0)
            leg.SetTextSize(0.045)  # Larger text size
            leg.SetTextFont(42)
            if h_or.GetEntries() > 0:
                leg.AddEntry(h_or, f"{trig1_display} || {trig2_display}", "l")
            if h_1.GetEntries() > 0:
                leg.AddEntry(h_1, trig1_display or "Trigger 1", "l")
            if h_2.GetEntries() > 0:
                leg.AddEntry(h_2, trig2_display or "Trigger 2", "l")
            leg.Draw()
            
            add_cms_label(c, f"{year}, {lumi:.1f} fb^{{-1}}" if lumi > 0 else f"{year}", 
                         "Simulation" if is_mc else "", trigger_text)
            plots.append((c, [h_or, h_1, h_2], f"{name}.png"))

    # Triphoton invariant mass
    mass_vars = [
        ("Maaa", 100, 0, 500, "M(#gamma#gamma#gamma) [GeV]", "Events / 5 GeV"),
        ("M_p1p2", 100, 0, 400, "M(#gamma_{1}#gamma_{2}) [GeV]", "Events / 4 GeV"),
    ]

    for var, nbins, xmin, xmax, xtitle, ytitle in mass_vars:
        # Create three histograms for overlay
        h_or = ROOT.TH1F(f"h_{var}_or", "", nbins, xmin, xmax)
        h_1 = ROOT.TH1F(f"h_{var}_1", "", nbins, xmin, xmax)
        h_2 = ROOT.TH1F(f"h_{var}_2", "", nbins, xmin, xmax)
        
        for h in [h_or, h_1, h_2]:
            h.Sumw2()
        
        combined_selection_or = f"({var} > 0) && ({trigger_selection_or})"
        combined_selection_1 = f"({var} > 0) && ({trigger_selection_1})"
        combined_selection_2 = f"({var} > 0) && ({trigger_selection_2})"
        
        chain.Draw(f"{var}>>h_{var}_or", f"{weight_expr} * ({combined_selection_or})", "goff")
        chain.Draw(f"{var}>>h_{var}_1", f"{weight_expr} * ({combined_selection_1})", "goff")
        chain.Draw(f"{var}>>h_{var}_2", f"{weight_expr} * ({combined_selection_2})", "goff")

        if h_or.GetEntries() > 0 or h_1.GetEntries() > 0 or h_2.GetEntries() > 0:
            c = create_canvas(f"c_{var}", var)
            
            style_histogram(h_or, "", xtitle, ytitle, ROOT.kBlack)
            style_histogram(h_1, "", xtitle, ytitle, ROOT.kRed+1)
            style_histogram(h_2, "", xtitle, ytitle, ROOT.kBlue+1)
            
            h_or.SetLineStyle(1)
            h_1.SetLineStyle(2)
            h_2.SetLineStyle(3)
            
            # Auto-scale y-axis for all histograms (with log scale)
            hist_list = [h_or]
            if h_1.GetEntries() > 0:
                hist_list.append(h_1)
            if h_2.GetEntries() > 0:
                hist_list.append(h_2)
            auto_scale_histograms(hist_list, pad_factor=1.2, log_scale=True)
            
            c.SetLogy()  # Log scale for mass
            
            h_or.Draw("HIST E")
            if h_1.GetEntries() > 0:
                h_1.Draw("HIST E SAME")
            if h_2.GetEntries() > 0:
                h_2.Draw("HIST E SAME")
            
            leg = ROOT.TLegend(0.60, 0.60, 0.92, 0.92)
            leg.SetBorderSize(0)
            leg.SetFillStyle(0)
            leg.SetTextSize(0.045)  # Larger text size
            leg.SetTextFont(42)
            if h_or.GetEntries() > 0:
                leg.AddEntry(h_or, f"{trig1_display} || {trig2_display}", "l")
            if h_1.GetEntries() > 0:
                leg.AddEntry(h_1, trig1_display or "Trigger 1", "l")
            if h_2.GetEntries() > 0:
                leg.AddEntry(h_2, trig2_display or "Trigger 2", "l")
            leg.Draw()
            
            add_cms_label(c, f"{year}, {lumi:.1f} fb^{{-1}}" if lumi > 0 else f"{year}", 
                         "Simulation" if is_mc else "", trigger_text)
            plots.append((c, [h_or, h_1, h_2], f"{var}.png"))

    # Scale factors and weights (MC only)
    if is_mc:
        sf_vars = [
            ("Photon_CutBased_MediumID_SF[0]", 50, 0.8, 1.2, "Leading photon Medium ID SF", "Events"),
            ("Photon_CutBased_TightID_SF[0]", 50, 0.8, 1.2, "Leading photon Tight ID SF", "Events"),
            ("puWeight", 50, 0, 3, "Pileup weight", "Events"),
            ("genWeight", 100, -2, 2, "Generator weight", "Events"),
        ]

        # Use unweighted for SF plots to see actual SF distributions (no trigger selection needed)
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
                plots.append((c, [h], f"{name}.png"))

    # Save all plots
    for canvas, hists, filename in plots:
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

def plot_2d_distributions(chain, output_dir, year, is_mc, lumi=1.0, trigger_type="none",
                          triple_photon_trigger1=None, triple_photon_trigger2=None):
    """Create 2D distribution plots with trigger selection (using OR for 2D)"""
    trigger_label = trigger_type.replace("_", " ").title() if trigger_type != "none" else "No Trigger"
    print(f"Creating 2D distributions (Trigger: {trigger_label})...")

    weight_expr = get_weight_expression(is_mc, include_sf=True)
    trigger_selection = get_trigger_selection(trigger_type, triple_photon_trigger1, triple_photon_trigger2)
    
    # Build trigger text for plots (use normalized names for display)
    trigger_text = ""
    trig1_display = normalize_trigger_name(triple_photon_trigger1) if triple_photon_trigger1 else None
    trig2_display = normalize_trigger_name(triple_photon_trigger2) if triple_photon_trigger2 else None
    
    if trigger_type == "triple_or":
        if trig1_display and trig2_display:
            trigger_text = f"Trigger: {trig1_display} || {trig2_display}"
        else:
            trigger_text = "Trigger: Any Triple Photon"
    elif trigger_type == "none":
        trigger_text = "No Trigger"
    else:
        trigger_text = f"Trigger: {trigger_label}"
    
    plots = []

    # Photon pT vs eta
    h2d_pt_eta = ROOT.TH2F("h2d_photon_pt_eta", "", 50, -2.5, 2.5, 50, 20, 300)
    combined_selection = f"(Photon_pt[0] > 20) && ({trigger_selection})"
    chain.Draw("Photon_pt[0]:Photon_eta[0]>>h2d_photon_pt_eta",
               f"{weight_expr} * ({combined_selection})", "goff")

    if h2d_pt_eta.GetEntries() > 0:
        c = create_canvas("c_photon_pt_eta", "photon_pt_eta", 900, 700)
        c.SetRightMargin(0.15)
        h2d_pt_eta.SetTitle("")
        h2d_pt_eta.GetXaxis().SetTitle("Leading photon #eta")
        h2d_pt_eta.GetYaxis().SetTitle("Leading photon p_{T} [GeV]")
        h2d_pt_eta.Draw("COLZ")
        add_cms_label(c, f"{year}, {lumi:.1f} fb^{{-1}}" if lumi > 0 else f"{year}", 
                     "Simulation" if is_mc else "", trigger_text)
        plots.append((c, h2d_pt_eta, "photon_pt_vs_eta.png"))

    # Photon eta vs phi
    h2d_eta_phi = ROOT.TH2F("h2d_photon_eta_phi", "", 50, -2.5, 2.5, 50, -3.15, 3.15)
    combined_selection = f"(Photon_pt[0] > 20) && ({trigger_selection})"
    chain.Draw("Photon_phi[0]:Photon_eta[0]>>h2d_photon_eta_phi",
               f"{weight_expr} * ({combined_selection})", "goff")

    if h2d_eta_phi.GetEntries() > 0:
        c = create_canvas("c_photon_eta_phi", "photon_eta_phi", 900, 700)
        c.SetRightMargin(0.15)
        h2d_eta_phi.SetTitle("")
        h2d_eta_phi.GetXaxis().SetTitle("Leading photon #eta")
        h2d_eta_phi.GetYaxis().SetTitle("Leading photon #phi")
        h2d_eta_phi.Draw("COLZ")
        add_cms_label(c, f"{year}, {lumi:.1f} fb^{{-1}}" if lumi > 0 else f"{year}", 
                     "Simulation" if is_mc else "", trigger_text)
        plots.append((c, h2d_eta_phi, "photon_eta_vs_phi.png"))

    # Di-photon mass vs tri-photon mass
    h2d_mass = ROOT.TH2F("h2d_diphoton_triphoton_mass", "", 50, 0, 400, 50, 0, 500)
    combined_selection = f"(Maaa > 0 && M_p1p2 > 0) && ({trigger_selection})"
    chain.Draw("Maaa:M_p1p2>>h2d_diphoton_triphoton_mass",
               f"{weight_expr} * ({combined_selection})", "goff")

    if h2d_mass.GetEntries() > 0:
        c = create_canvas("c_diphoton_triphoton_mass", "mass_correlation", 900, 700)
        c.SetRightMargin(0.15)
        c.SetLogz()
        h2d_mass.SetTitle("")
        h2d_mass.GetXaxis().SetTitle("M(#gamma_{1}#gamma_{2}) [GeV]")
        h2d_mass.GetYaxis().SetTitle("M(#gamma#gamma#gamma) [GeV]")
        h2d_mass.Draw("COLZ")
        add_cms_label(c, f"{year}, {lumi:.1f} fb^{{-1}}" if lumi > 0 else f"{year}", 
                     "Simulation" if is_mc else "", trigger_text)
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
    parser.add_argument("--data", action="store_true", 
                       help="Input is data (not MC). Note: Triggers are applied to BOTH data and MC for proper comparison.")
    parser.add_argument("--max-files", type=int, default=None, help="Maximum number of files to process")
    parser.add_argument("--no-html", action="store_true", help="Don't create HTML index file")
    parser.add_argument("--triple-trigger1", default="HLT_TriplePhoton_30_30_10_CaloIdLV2",
                       help="First triple photon trigger name", dest="triple_trigger1")
    parser.add_argument("--triple-trigger2", default="HLT_TriplePhoton_30_30_10_CaloIdLV2_R9IdVL",
                       help="Second triple photon trigger name", dest="triple_trigger2")
    parser.add_argument("--no-trigger", action="store_true",
                       help="Don't apply triggers (for debugging only)")
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
    
    # Important: Triggers are applied to BOTH data and MC for proper comparison
    # MC events are filtered by the same triggers that would fire in data
    if not args.no_trigger:
        if is_mc:
            print(f"\n{'='*60}")
            print("IMPORTANT: Applying trigger selection to MC")
            print("This ensures MC plots are comparable to data plots")
            print(f"Creating overlay plots with:")
            print(f"  - Nominal: {args.triple_trigger1} || {args.triple_trigger2}")
            print(f"  - Trigger 1: {args.triple_trigger1}")
            print(f"  - Trigger 2: {args.triple_trigger2}")
            print(f"{'='*60}\n")
        else:
            print(f"\n{'='*60}")
            print("Applying trigger selection to DATA")
            print(f"Creating overlay plots with:")
            print(f"  - Nominal: {args.triple_trigger1} || {args.triple_trigger2}")
            print(f"  - Trigger 1: {args.triple_trigger1}")
            print(f"  - Trigger 2: {args.triple_trigger2}")
            print(f"{'='*60}\n")
    else:
        print(f"\n{'='*60}")
        print("WARNING: No trigger selection applied (--no-trigger flag used)")
        print(f"{'='*60}\n")
    
    # Create overlay plots with all three trigger selections
    plot_1d_distributions(chain, args.output, args.year, is_mc, args.lumi,
                         triple_photon_trigger1=args.triple_trigger1,
                         triple_photon_trigger2=args.triple_trigger2,
                         no_trigger=args.no_trigger)
    
    # For 2D plots, we can still use the OR selection (or make them overlay too)
    # For now, let's use OR for 2D plots
    plot_2d_distributions(chain, args.output, args.year, is_mc, args.lumi,
                         trigger_type="triple_or" if not args.no_trigger else "none",
                         triple_photon_trigger1=args.triple_trigger1,
                         triple_photon_trigger2=args.triple_trigger2)

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
