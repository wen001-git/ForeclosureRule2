// One-time transform: add per-servicer `servicers` map to multi-servicer fields, drop free-text `carrington`.
// Run: node scripts/_add_servicers.js   (re-runnable / idempotent)
const fs = require("fs");
const P = "outputs/fcl_lineage_source.json";
const J = JSON.parse(fs.readFileSync(P, "utf8"));
const D = "—";
// keyed by label.en
const MAP = {
  // --- main: milestones ---
  "Notice of Intent Date": ["—", "—", "portcapecodfive_monthly_collections.noi_date"],
  "Referred to Foreclosure (Referral)": ["portnewrezfc.fcreferraldate", "portcarrington.fcl_referral_date", "portcapecodfive_monthly_collections.foreclosure_date_refrd_atty"],
  "Title Report Received": ["portnewrezfc.titlereceiveddate", "—", "—"],
  "Preliminary Title Cleared": ["portnewrezfc.titlecleardate", "—", "—"],
  "1st Legal": ["portnewrezfc.firstlegaldate", "—", "portcapecodfive_monthly_collections.foreclosure_first_legal_date"],
  "Service Complete": ["portnewrezfc.servicecompletedate", "—", "portcapecodfive_monthly_collections.foreclosure_service_date"],
  "Judgement Hearing Set": ["portnewrezfc.fcjudgmenthearingscheduled", "—", "—"],
  "Judgement": ["portnewrezfc.fcjudgmenthearingscheduled", "—", "—"],
  "Sale Date Projected": ["portnewrezfc.fcscheduledsaledate", "portcarrington.fcl_scheduled_sale_date", "portcapecodfive_monthly_collections.foreclosure_date_sale_scheduled"],
  "Sale Date Set": ["portnewrezfc.fcscheduledsaledate", "portcarrington.fcl_scheduled_sale_date", "portcapecodfive_monthly_collections.foreclosure_date_sale_scheduled"],
  "Final Title Cleared": ["portnewrezfc.titlecleardate", "—", "—"],
  "Sale Held": ["portnewrezfc.fcsalehelddate", "portcarrington.fcl_sale_held_date", "portcapecodfive_monthly_collections.foreclosure_sale_date"],
  "3rd Party Proceeds Received": ["portnewrezfc.fcl3rdpartyproceedsreceiveddate", "—", "—"],
  "3rd Party Sold Date": ["—", "—", "—"],
  // --- main: summary/status ---
  "Foreclosure Status": ["portnewrezfc.activefcflag + fcremovaldesc", "portcarrington.fcl_flag (activefcflag CASE)", "portcapecodfive_monthly_collections.foreclosure_flag (activefcflag CASE)"],
  "Type (Judicial / Non Judicial)": ["portnewrezfc.judicial", "—", "—"],
  "Judicial Foreclosure (flag)": ["portnewrezfc.judicial", "—", "—"],
  "Firm": ["portnewrezfc.fcfirm", "portcarrington.fcl_attorney_name", "—"],
  "Foreclosure Bid Amount": ["portnewrezfc.fcbidamount", "—", "—"],
  "Foreclosure Sale Amount": ["portnewrezfc.fcsaleamount", "—", "—"],
  "SMS Days in Foreclosure": ["portnewrezfc.smsdaysinfc", "—", "—"],
  "Days in Foreclosure": ["portnewrezfc.daysinfc", "(computed: datediff(referral,snapshot)+1)", "(computed: datediff(referral,dataasof)+1)"],
  "Current Step": ["portnewrezfc.fcstage", "portcarrington.fcl_sub_status", "—"],
  "Last Step Completed": ["portnewrezfc.lastfcstepcompleted", "—", "portcapecodfive_monthly_collections.most_recent_foreclosure_stage"],
  "Last Step Completed Date": ["portnewrezfc.lastfcstepcompleteddate", "—", "—"],
  "Contested / Litigation": ["portnewrezfc.fccontestedflag", "—", "—"],
  // --- stage: dims ---
  "Group (FCL/D120P/D90/REO/P…)": ["portnewrezgeneral.delinquency_status_mba (+portnewrezpmt.nextduedate · days360)", "portcarrington.loan_status / fcl_flag (+date_payment_due · days360)", "—"],
  "Judicial (Y/N)": ["portnewrezfc.judicial", "— (state fallback 州级回退)", "— (state fallback 州级回退)"],
  "State": ["portnewrezprop.propertystate", "portcarrington.property_state", "—"],
  // --- stage: dates (one summary row covering all stages) ---
  "{stage}_start_date (referral/first_legal/service/judgement/sale/demand)": [
    "portnewrezfc.{fcreferraldate / firstlegaldate / servicecompletedate / fcjudgmenthearingscheduled / fcscheduledsaledate / demandsentdate}",
    "portcarrington.{fcl_referral_date / fcl_scheduled_sale_date / fcl_sale_held_date}",
    "portcapecodfive_monthly_collections.{foreclosure_date_refrd_atty / foreclosure_first_legal_date / foreclosure_service_date / foreclosure_date_sale_scheduled}"
  ],
  // --- hold ---
  "Description / Start / End (unpivot)": ["portnewrezfc.fchold1..3 {description, startdate, enddate}", "portcarrington fchold4 slot (dates only)", "—"]
};
let added = 0, removed = 0, miss = [];
J.fields.forEach(f => {
  if ("carrington" in f) { delete f.carrington; removed++; }
  const lab = f.label && f.label.en;
  if (MAP[lab]) {
    const [n, c, cc] = MAP[lab];
    f.servicers = { Newrez: n, Carrington: c, Capecodfive: cc };
    added++;
  }
});
// sanity: which MAP keys were not matched
Object.keys(MAP).forEach(k => { if (!J.fields.some(f => f.label && f.label.en === k)) miss.push(k); });
fs.writeFileSync(P, JSON.stringify(J, null, 2) + "\n");
console.log("servicers added:", added, "| carrington removed:", removed, "| unmatched MAP keys:", miss.length ? miss : "none");
