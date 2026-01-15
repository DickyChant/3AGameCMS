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
        CMS.SetLumi("")
    
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

def normalize_trigger_name(trigger_name):
    """Remove _v suffix from trigger names if present"""
    if trigger_name and trigger_name.endswith("_v"):
        return trigger_name[:-2]  # Remove "_v" suffix
    return trigger_name

def get_trigger_selection(trigger_type="none", triple_photon_trigger1=None, triple_photon_trigger2=None):
    """
    Build trigger selection string
    
    Args:
        trigger_type: "none", "triple1", "triple2", "triple_or", "diphoton"
        triple_photon_trigger1: First triple photon trigger name
        triple_photon_trigger2: Second triple photon trigger name
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
            return "(HLT_passAnyTriplePhoton == 1)"
    
    if trigger_type == "diphoton":
        # Diphoton triggers, but exclude events where triple photon triggers fired
        return "(HLT_passAnyDiphoton == 1 && HLT_passAnyTriplePhoton == 0)"
    
    return "1"

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
    # Add trigger text (bottom left) if provided
    if trigger_text:
        latex = ROOT.TLatex()
        latex.SetNDC()
        latex.SetTextFont(42)
        latex.SetTextSize(0.035)
        latex.SetTextAlign(11)  # Left-aligned
        latex.DrawLatex(0.15, 0.15, trigger_text)

def plot_triphoton_kinematics(chain, output_dir, year, is_mc, lumi, 
                              triple_photon_trigger1=None, triple_photon_trigger2=None, no_trigger=False):
    """Plot triphoton kinematics for events with exactly 3 photons, with trigger overlays"""
    print("Creating triphoton (3γ) kinematic plots with trigger overlays...")

    weight_expr = "(genWeight > 0 ? 1 : -1) * puWeight" if is_mc else "1"
    base_selection = "nGoodPhoton >= 3"
    
    # Get trigger selections
    if no_trigger:
        trigger_selection_or = "1"
        trigger_selection_1 = "1"
        trigger_selection_2 = "1"
        trig1_display = "All Events"
        trig2_display = "All Events"
        trigger_text = "No Trigger"
    else:
        trigger_selection_or = get_trigger_selection("triple_or", triple_photon_trigger1, triple_photon_trigger2)
        trigger_selection_1 = get_trigger_selection("triple1", triple_photon_trigger1, triple_photon_trigger2)
        trigger_selection_2 = get_trigger_selection("triple2", triple_photon_trigger1, triple_photon_trigger2)
        trig1_display = normalize_trigger_name(triple_photon_trigger1) if triple_photon_trigger1 else None
        trig2_display = normalize_trigger_name(triple_photon_trigger2) if triple_photon_trigger2 else None
        if trig1_display and trig2_display:
            trigger_text = f"Triggers: {trig1_display} || {trig2_display}"
        else:
            trigger_text = "Triple Photon Triggers"

    plots = []

    # Three photon pT distributions on same canvas - with trigger overlays
    # For each photon, create three histograms (OR, triple1, triple2)
    h_pt = []
    for i in range(3):
        h_or = ROOT.TH1F(f"h_pt_g{i+1}_or", "", 50, 20, 200)
        h_1 = ROOT.TH1F(f"h_pt_g{i+1}_1", "", 50, 20, 200)
        h_2 = ROOT.TH1F(f"h_pt_g{i+1}_2", "", 50, 20, 200)
        for h in [h_or, h_1, h_2]:
            h.Sumw2()
        
        selection_i = f"(nGoodPhoton > {i})"
        combined_or = f"({selection_i}) && ({trigger_selection_or})"
        combined_1 = f"({selection_i}) && ({trigger_selection_1})"
        combined_2 = f"({selection_i}) && ({trigger_selection_2})"
        
        chain.Draw(f"Photon_pt[{i}]>>h_pt_g{i+1}_or", f"{weight_expr} * ({combined_or})", "goff")
        chain.Draw(f"Photon_pt[{i}]>>h_pt_g{i+1}_1", f"{weight_expr} * ({combined_1})", "goff")
        chain.Draw(f"Photon_pt[{i}]>>h_pt_g{i+1}_2", f"{weight_expr} * ({combined_2})", "goff")
        
        h_pt.append([h_or, h_1, h_2])
    
    colors = [ROOT.kRed+1, ROOT.kBlue+1, ROOT.kGreen+2]
    labels = ["Leading #gamma", "Subleading #gamma", "Third #gamma"]
    
    # Create overlay plots for each photon
    for i in range(3):
        h_or, h_1, h_2 = h_pt[i]
        
        if h_or.GetEntries() > 0 or h_1.GetEntries() > 0 or h_2.GetEntries() > 0:
            c = create_canvas(f"c_photon{i+1}_pt", f"photon{i+1}_pt")
            
            style_histogram(h_or, "", f"Photon {i+1} p_{{T}} [GeV]", "Events / 3.6 GeV", ROOT.kBlack)
            style_histogram(h_1, "", f"Photon {i+1} p_{{T}} [GeV]", "Events / 3.6 GeV", ROOT.kRed+1)
            style_histogram(h_2, "", f"Photon {i+1} p_{{T}} [GeV]", "Events / 3.6 GeV", ROOT.kBlue+1)
            
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
            leg.SetTextSize(0.045)
            leg.SetTextFont(42)
            if not no_trigger:
                if h_or.GetEntries() > 0:
                    leg.AddEntry(h_or, f"{trig1_display} || {trig2_display}", "l")
                if h_1.GetEntries() > 0:
                    leg.AddEntry(h_1, trig1_display or "Trigger 1", "l")
                if h_2.GetEntries() > 0:
                    leg.AddEntry(h_2, trig2_display or "Trigger 2", "l")
            else:
                if h_or.GetEntries() > 0:
                    leg.AddEntry(h_or, "All Events", "l")
            leg.Draw()
            
            add_cms_label(c, f"{year}, {lumi:.1f} fb^{{-1}}" if lumi > 0 else f"{year}", 
                         "Simulation" if is_mc else "", trigger_text)
            plots.append((c, [h_or, h_1, h_2], f"photon{i+1}_pt.png"))
    
    # Also create comparison plot with all three photons (using OR trigger)
    c_pt = create_canvas("c_triphoton_pt", "triphoton_pt")
    photon_colors = [ROOT.kRed+1, ROOT.kBlue+1, ROOT.kGreen+2]
    photon_labels = ["Leading #gamma", "Subleading #gamma", "Third #gamma"]
    pt_hist_list = []
    for i in range(3):
        h_or, _, _ = h_pt[i]
        style_histogram(h_or, "", "Photon p_{T} [GeV]", "Events / 3.6 GeV", photon_colors[i])
        pt_hist_list.append(h_or)
    
    # Auto-scale for comparison plot
    auto_scale_histograms(pt_hist_list, pad_factor=1.2, log_scale=False)
    
    for i in range(3):
        h_or, _, _ = h_pt[i]
        if i == 0:
            h_or.Draw("HIST E")
        else:
            h_or.Draw("HIST E SAME")
    
    leg = ROOT.TLegend(0.60, 0.60, 0.92, 0.92)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextSize(0.045)
    leg.SetTextFont(42)
    for i in range(3):
        leg.AddEntry(h_pt[i][0], photon_labels[i], "l")
    leg.Draw()
    add_cms_label(c_pt, f"{year}, {lumi:.1f} fb^{{-1}}" if lumi > 0 else f"{year}", 
                 "Simulation" if is_mc else "", trigger_text)
    plots.append((c_pt, [h[0] for h in h_pt], "triphoton_pt_comparison.png"))

    # Three photon eta distributions with trigger overlays
    h_eta = []
    for i in range(3):
        h_or = ROOT.TH1F(f"h_eta_g{i+1}_or", "", 50, -2.5, 2.5)
        h_1 = ROOT.TH1F(f"h_eta_g{i+1}_1", "", 50, -2.5, 2.5)
        h_2 = ROOT.TH1F(f"h_eta_g{i+1}_2", "", 50, -2.5, 2.5)
        for h in [h_or, h_1, h_2]:
            h.Sumw2()
        
        selection_i = f"(nGoodPhoton > {i})"
        combined_or = f"({selection_i}) && ({trigger_selection_or})"
        combined_1 = f"({selection_i}) && ({trigger_selection_1})"
        combined_2 = f"({selection_i}) && ({trigger_selection_2})"
        
        chain.Draw(f"Photon_eta[{i}]>>h_eta_g{i+1}_or", f"{weight_expr} * ({combined_or})", "goff")
        chain.Draw(f"Photon_eta[{i}]>>h_eta_g{i+1}_1", f"{weight_expr} * ({combined_1})", "goff")
        chain.Draw(f"Photon_eta[{i}]>>h_eta_g{i+1}_2", f"{weight_expr} * ({combined_2})", "goff")
        
        h_eta.append([h_or, h_1, h_2])
    
    # Create overlay plot for eta comparison (using OR trigger)
    c_eta = create_canvas("c_triphoton_eta", "triphoton_eta")
    eta_hist_list = []
    for i in range(3):
        h_or, _, _ = h_eta[i]
        style_histogram(h_or, "", "Photon #eta", "Events", photon_colors[i])
        eta_hist_list.append(h_or)
    
    # Auto-scale for comparison plot
    auto_scale_histograms(eta_hist_list, pad_factor=1.2, log_scale=False)
    
    for i in range(3):
        h_or, _, _ = h_eta[i]
        if i == 0:
            h_or.Draw("HIST E")
        else:
            h_or.Draw("HIST E SAME")
    
    leg_eta = ROOT.TLegend(0.60, 0.60, 0.92, 0.92)
    leg_eta.SetBorderSize(0)
    leg_eta.SetFillStyle(0)
    leg_eta.SetTextSize(0.045)
    leg_eta.SetTextFont(42)
    for i in range(3):
        leg_eta.AddEntry(h_eta[i][0], photon_labels[i], "l")
    leg_eta.Draw()
    add_cms_label(c_eta, f"{year}, {lumi:.1f} fb^{{-1}}" if lumi > 0 else f"{year}", 
                 "Simulation" if is_mc else "", trigger_text)
    plots.append((c_eta, [h[0] for h in h_eta], "triphoton_eta_comparison.png"))

    # Save all plots
    for canvas, hist, filename in plots:
        canvas.SaveAs(os.path.join(output_dir, filename))
        canvas.SaveAs(os.path.join(output_dir, filename.replace(".png", ".pdf")))

    print(f"Saved {len(plots)} triphoton kinematic plots")

def plot_invariant_masses(chain, output_dir, year, is_mc, lumi,
                          triple_photon_trigger1=None, triple_photon_trigger2=None, no_trigger=False):
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

    # Get trigger selections
    if no_trigger:
        trigger_selection_or = "1"
        trigger_selection_1 = "1"
        trigger_selection_2 = "1"
        trig1_display = "All Events"
        trig2_display = "All Events"
        trigger_text = "No Trigger"
    else:
        trigger_selection_or = get_trigger_selection("triple_or", triple_photon_trigger1, triple_photon_trigger2)
        trigger_selection_1 = get_trigger_selection("triple1", triple_photon_trigger1, triple_photon_trigger2)
        trigger_selection_2 = get_trigger_selection("triple2", triple_photon_trigger1, triple_photon_trigger2)
        trig1_display = normalize_trigger_name(triple_photon_trigger1) if triple_photon_trigger1 else None
        trig2_display = normalize_trigger_name(triple_photon_trigger2) if triple_photon_trigger2 else None
        if trig1_display and trig2_display:
            trigger_text = f"Triggers: {trig1_display} || {trig2_display}"
        else:
            trigger_text = "Triple Photon Triggers"
    
    # Create histograms for trigger overlays
    h_m12_or = ROOT.TH1F("h_m12_or", "", 100, 0, 300)
    h_m12_1 = ROOT.TH1F("h_m12_1", "", 100, 0, 300)
    h_m12_2 = ROOT.TH1F("h_m12_2", "", 100, 0, 300)
    h_m123_or = ROOT.TH1F("h_m123_or", "", 100, 0, 500)
    h_m123_1 = ROOT.TH1F("h_m123_1", "", 100, 0, 500)
    h_m123_2 = ROOT.TH1F("h_m123_2", "", 100, 0, 500)
    
    for h in [h_m12_or, h_m12_1, h_m12_2, h_m123_or, h_m123_1, h_m123_2]:
        h.Sumw2()
    
    # Calculate masses event-by-event with trigger selection
    print("  Processing events...")
    n_events = 0
    for event in chain:
        if event.nGoodPhoton < 3:
            continue

        # Check triggers using getattr (safer than eval)
        if no_trigger:
            pass_or = pass_1 = pass_2 = True
        else:
            # Helper function to check trigger
            def check_trigger(trigger_expr):
                if trigger_expr == "1":
                    return True
                # Parse expressions like "(HLT_TriplePhoton_30_30_10_CaloIdLV2 == 1)"
                # or "((HLT_TriplePhoton_30_30_10_CaloIdLV2 == 1) || (HLT_TriplePhoton_35_35_5_CaloIdLV2_R9IdVL == 1))"
                try:
                    # Simple case: single trigger
                    if "||" not in trigger_expr:
                        trigger_name = trigger_expr.split("==")[0].strip().strip("(").strip()
                        return getattr(event, trigger_name, 0) == 1
                    else:
                        # OR case: check both triggers
                        parts = trigger_expr.split("||")
                        result = False
                        for part in parts:
                            trigger_name = part.split("==")[0].strip().strip("(").strip()
                            if getattr(event, trigger_name, 0) == 1:
                                result = True
                                break
                        return result
                except:
                    return True  # Default to True if parsing fails
            
            pass_or = check_trigger(trigger_selection_or)
            pass_1 = check_trigger(trigger_selection_1)
            pass_2 = check_trigger(trigger_selection_2)
        
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

        m12 = (p1+p2).M()
        m123 = (p1+p2+p3).M()

        # Fill histograms based on trigger
        if pass_or:
            h_m12_or.Fill(m12, weight)
            h_m123_or.Fill(m123, weight)
        if pass_1:
            h_m12_1.Fill(m12, weight)
            h_m123_1.Fill(m123, weight)
        if pass_2:
            h_m12_2.Fill(m12, weight)
            h_m123_2.Fill(m123, weight)

        n_events += 1
        if n_events % 10000 == 0:
            print(f"    Processed {n_events} triphoton events...")

    print(f"  Total triphoton events: {n_events}")

    plots = []

    # Plot diphoton mass (M12) with trigger overlays
    c_diphoton = create_canvas("c_diphoton_mass", "diphoton_mass", 900, 700)
    style_histogram(h_m12_or, "", "M(#gamma_{1}#gamma_{2}) [GeV]", "Events / 3 GeV", ROOT.kBlack)
    style_histogram(h_m12_1, "", "M(#gamma_{1}#gamma_{2}) [GeV]", "Events / 3 GeV", ROOT.kRed+1)
    style_histogram(h_m12_2, "", "M(#gamma_{1}#gamma_{2}) [GeV]", "Events / 3 GeV", ROOT.kBlue+1)
    
    h_m12_or.SetLineStyle(1)
    h_m12_1.SetLineStyle(2)
    h_m12_2.SetLineStyle(3)
    
    # Auto-scale y-axis for all histograms
    hist_list = [h_m12_or]
    if h_m12_1.GetEntries() > 0:
        hist_list.append(h_m12_1)
    if h_m12_2.GetEntries() > 0:
        hist_list.append(h_m12_2)
    auto_scale_histograms(hist_list, pad_factor=1.2, log_scale=False)
    
    h_m12_or.Draw("HIST E")
    if h_m12_1.GetEntries() > 0:
        h_m12_1.Draw("HIST E SAME")
    if h_m12_2.GetEntries() > 0:
        h_m12_2.Draw("HIST E SAME")
    
    leg = ROOT.TLegend(0.60, 0.60, 0.92, 0.92)
    leg.SetTextSize(0.045)
    leg.SetTextFont(42)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    if not no_trigger:
        if h_m12_or.GetEntries() > 0:
            leg.AddEntry(h_m12_or, f"{trig1_display} || {trig2_display}", "l")
        if h_m12_1.GetEntries() > 0:
            leg.AddEntry(h_m12_1, trig1_display or "Trigger 1", "l")
        if h_m12_2.GetEntries() > 0:
            leg.AddEntry(h_m12_2, trig2_display or "Trigger 2", "l")
    else:
        if h_m12_or.GetEntries() > 0:
            leg.AddEntry(h_m12_or, "All Events", "l")
    leg.Draw()
    
    add_cms_label(c_diphoton, f"{year}, {lumi:.1f} fb^{{-1}}" if lumi > 0 else f"{year}", 
                 "Simulation" if is_mc else "", trigger_text)
    plots.append((c_diphoton, [h_m12_or, h_m12_1, h_m12_2], "diphoton_mass_m12.png"))

    # Plot triphoton mass with trigger overlays
    c_triphoton = create_canvas("c_triphoton_mass", "triphoton_mass")
    style_histogram(h_m123_or, "", "M(#gamma#gamma#gamma) [GeV]", "Events / 5 GeV", ROOT.kBlack)
    style_histogram(h_m123_1, "", "M(#gamma#gamma#gamma) [GeV]", "Events / 5 GeV", ROOT.kRed+1)
    style_histogram(h_m123_2, "", "M(#gamma#gamma#gamma) [GeV]", "Events / 5 GeV", ROOT.kBlue+1)
    
    h_m123_or.SetLineStyle(1)
    h_m123_1.SetLineStyle(2)
    h_m123_2.SetLineStyle(3)
    
    # Auto-scale y-axis for all histograms (with log scale)
    hist_list = [h_m123_or]
    if h_m123_1.GetEntries() > 0:
        hist_list.append(h_m123_1)
    if h_m123_2.GetEntries() > 0:
        hist_list.append(h_m123_2)
    auto_scale_histograms(hist_list, pad_factor=1.2, log_scale=True)
    
    c_triphoton.SetLogy()
    
    h_m123_or.Draw("HIST E")
    if h_m123_1.GetEntries() > 0:
        h_m123_1.Draw("HIST E SAME")
    if h_m123_2.GetEntries() > 0:
        h_m123_2.Draw("HIST E SAME")
    
    leg2 = ROOT.TLegend(0.60, 0.60, 0.92, 0.92)
    leg2.SetTextSize(0.045)
    leg2.SetTextFont(42)
    leg2.SetBorderSize(0)
    leg2.SetFillStyle(0)
    if not no_trigger:
        if h_m123_or.GetEntries() > 0:
            leg2.AddEntry(h_m123_or, f"{trig1_display} || {trig2_display}", "l")
        if h_m123_1.GetEntries() > 0:
            leg2.AddEntry(h_m123_1, trig1_display or "Trigger 1", "l")
        if h_m123_2.GetEntries() > 0:
            leg2.AddEntry(h_m123_2, trig2_display or "Trigger 2", "l")
    else:
        if h_m123_or.GetEntries() > 0:
            leg2.AddEntry(h_m123_or, "All Events", "l")
    leg2.Draw()
    
    add_cms_label(c_triphoton, f"{year}, {lumi:.1f} fb^{{-1}}" if lumi > 0 else f"{year}", 
                 "Simulation" if is_mc else "", trigger_text)
    plots.append((c_triphoton, [h_m123_or, h_m123_1, h_m123_2], "triphoton_invariant_mass.png"))

    # 2D correlation: leading diphoton mass vs triphoton mass (using OR trigger)
    h2d_m12_m123 = ROOT.TH2F("h2d_m12_m123", "", 60, 0, 300, 60, 0, 500)

    for event in chain:
        if event.nGoodPhoton < 3:
            continue
        
        # Check trigger (use OR for 2D plot)
        if not no_trigger:
            def check_trigger(trigger_expr):
                if trigger_expr == "1":
                    return True
                try:
                    if "||" not in trigger_expr:
                        trigger_name = trigger_expr.split("==")[0].strip().strip("(").strip()
                        return getattr(event, trigger_name, 0) == 1
                    else:
                        parts = trigger_expr.split("||")
                        for part in parts:
                            trigger_name = part.split("==")[0].strip().strip("(").strip()
                            if getattr(event, trigger_name, 0) == 1:
                                return True
                        return False
                except:
                    return True
            if not check_trigger(trigger_selection_or):
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
    add_cms_label(c_2d, f"{year}, {lumi:.1f} fb^{{-1}}" if lumi > 0 else f"{year}", 
                 "Simulation" if is_mc else "", trigger_text)
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
    parser.add_argument("--triple-trigger1", default="HLT_TriplePhoton_30_30_10_CaloIdLV2",
                       help="First triple photon trigger name", dest="triple_trigger1")
    parser.add_argument("--triple-trigger2", default="HLT_TriplePhoton_30_30_10_CaloIdLV2_R9IdVL",
                       help="Second triple photon trigger name", dest="triple_trigger2")
    parser.add_argument("--no-trigger", action="store_true",
                       help="Don't apply triggers (for debugging only)")
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
    plot_triphoton_kinematics(chain, args.output, args.year, is_mc, args.lumi,
                             triple_photon_trigger1=args.triple_trigger1,
                             triple_photon_trigger2=args.triple_trigger2,
                             no_trigger=args.no_trigger)
    plot_invariant_masses(chain, args.output, args.year, is_mc, args.lumi,
                         triple_photon_trigger1=args.triple_trigger1,
                         triple_photon_trigger2=args.triple_trigger2,
                         no_trigger=args.no_trigger)
    create_html_index(args.output, args.year, is_mc, args.lumi)

    print(f"\nDone! Plots saved to {args.output}/")
    if "/eos/user/s/sqian/www/triphoton/" in args.output:
        timestamp_dir = os.path.basename(args.output)
        print(f"View at: https://sqian.web.cern.ch/triphoton/{timestamp_dir}/")

    return 0

if __name__ == "__main__":
    sys.exit(main())
