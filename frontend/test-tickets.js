// 20 sample tickets covering every routing category, plus a couple of edge
// cases (multi-issue, irrelevant) - used to quickly load an example into the
// ticket form instead of typing one from scratch.
const TEST_TICKETS = [
  {
    label: "Flight Disruption — Cancelled flight",
    text: "My flight from JFK to LAX was cancelled two hours before departure and I need to be rebooked on the next available flight.",
  },
  {
    label: "Flight Disruption — Delay causing missed connection",
    text: "My connecting flight is delayed by 3 hours and I'm going to miss my connection in Chicago.",
  },
  {
    label: "Baggage — Missing on arrival",
    text: "My checked baggage did not arrive with me at Miami airport and I have no idea where it is.",
  },
  {
    label: "Baggage — Damaged suitcase",
    text: "My suitcase came back from the flight with a broken wheel and a large tear in the fabric.",
  },
  {
    label: "Reservations & Ticketing — Date change",
    text: "I would like to change the date of my upcoming reservation from March 5th to March 12th.",
  },
  {
    label: "Reservations & Ticketing — Name correction",
    text: "There's a typo in my last name on my booking confirmation and I need it corrected before I fly.",
  },
  {
    label: "Refunds & Compensation — Cancelled flight refund",
    text: "My flight was cancelled and I don't want to be rebooked, I just want a full refund.",
  },
  {
    label: "Refunds & Compensation — Duplicate charge",
    text: "I was charged twice for the same ticket and I need the duplicate charge refunded.",
  },
  {
    label: "Payments & Billing — Card declined",
    text: "My credit card keeps getting declined when I try to pay for my ticket even though I have sufficient funds.",
  },
  {
    label: "Loyalty Program — Missing miles",
    text: "I flew three flights last month but none of the miles were credited to my frequent flyer account.",
  },
  {
    label: "Account & Identity Support — Login issue",
    text: "I can't log into my Skyfarer account, it keeps saying my password is incorrect even after I reset it.",
  },
  {
    label: "Accessibility & Special Services — Wheelchair assistance",
    text: "I use a wheelchair and I need to arrange assistance for boarding on my flight next week.",
  },
  {
    label: "Legal & Compliance — Discrimination allegation",
    text: "I was denied boarding and I believe it was because of my nationality, the staff treated me very differently from other passengers.",
  },
  {
    label: "Trust & Security — Account compromised",
    text: "I just noticed a booking on my account that I never made, I think someone has hacked into it.",
  },
  {
    label: "Safety & Compliance — In-flight incident",
    text: "During the flight, oxygen masks dropped unexpectedly and the crew didn't explain what was happening.",
  },
  {
    label: "Platform Engineering — App issue",
    text: "The mobile app crashes every time I try to check in for my flight online.",
  },
  {
    label: "Customer Relations — Service complaint",
    text: "The flight attendants on my last flight were incredibly rude and dismissive when I asked for water.",
  },
  {
    label: "Customer Support Desk — General question",
    text: "What is the maximum size allowed for a carry-on bag?",
  },
  {
    label: "Edge case — Multiple issues in one ticket",
    text: "My flight was delayed by 6 hours, I missed my connection, and now my baggage is lost too.",
  },
  {
    label: "Edge case — Irrelevant to airline support",
    text: "Can you recommend a good recipe for chocolate cake?",
  },
];
