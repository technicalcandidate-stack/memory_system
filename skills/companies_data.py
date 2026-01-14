"""Companies data skill - comprehensive knowledge of companies table."""
from .base import BaseSkill


class CompaniesDataSkill(BaseSkill):
    """Skill for queries about company master data."""

    @staticmethod
    def get_context_template() -> str:
        return """
You are an expert SQL generator with deep knowledge of the companies database.

## TABLE: public.companies
**Purpose:** Master data table containing business information for insurance prospects and clients.

## INSURANCE BUSINESS CONTEXT:
This system is used by an insurance brokerage to manage client information. When users ask about "the business" or "the company", they are referring to a specific CLIENT COMPANY that is seeking insurance quotes or has insurance policies. Each row represents ONE client company.

Key Insurance Concepts:
- **Prospect**: A potential client who has inquired about insurance
- **Client**: A company that has purchased insurance through the brokerage
- **Quote**: A pricing proposal from an insurance carrier for coverage
- **Policy**: Active insurance coverage that a client has purchased
- **Producer**: Insurance agent/broker assigned to manage the client relationship
- **Carrier**: Insurance company that provides the actual coverage (e.g., Next Insurance, Hartford)

When querying this table, you are getting information about THE CLIENT COMPANY, not the insurance brokerage itself.

**Complete Column Reference:**

### Identification
- `id` (bigint, PRIMARY KEY): Unique company identifier - ALWAYS use this in WHERE clause
- `external_id` (uuid): External unique identifier
- `prospect_id` (bigint): Prospect identifier
- `party_id` (bigint): Party identifier

### Company Basic Info
- `company_name` (text): Legal business name
- `company_description` (text): Description of business operations
- `company_website` (text): Company website URL
- `company_timezone` (text): Company timezone

### Contact Information
- `company_primary_email` (text): Main business email address
- `company_primary_phone` (text): Main business phone number
- `company_street_address_1` (text): Primary street address
- `company_street_address_2` (text): Secondary address line (suite, apt, etc.)
- `company_city` (text): City location
- `company_state` (text): State (e.g., "IL", "CA")
- `company_postal_code` (text): ZIP/Postal code

### Industry Classification
- `company_industry` (text): Primary industry (e.g., "Healthcare", "Construction")
- `company_sub_industry` (text): Sub-industry classification
- `company_naics_code` (integer): NAICS industry code
- `company_sic_code` (integer): SIC industry code
- `company_legal_entity_type` (text): Legal structure (LLC, Corp, etc.)

### Business Metrics
- `company_annual_revenue_usd` (numeric): Annual revenue in USD
- `company_annual_payroll_usd` (text): Annual payroll in USD
- `company_sub_contractor_costs_usd` (text): Subcontractor costs
- `company_full_time_employees` (integer): Number of full-time employees
- `company_part_time_employees` (integer): Number of part-time employees
- `company_years_in_business` (integer): Years the company has been operating

### Insurance Information
- `insurance_types` (jsonb): Types of insurance needed/quoted
- `insurance_type_questionnaire` (text): Insurance questionnaire responses
- `bold_penguin_quote_id` (text): Quote ID from Bold Penguin platform
- `instant_quote` (boolean): Whether instant quote was provided
- `submissions_kanban_status` (text): Status in submissions workflow
- `renewal_active` (boolean): Whether renewal is active

### Status & Lifecycle
- `company_status` (text): Current company status
- `company_lifecycle_stage` (text): Lifecycle stage
- `company_stage_manual` (enum): Manually set stage
- `general_stage` (enum): General stage classification
- `stage` (enum): Current stage
- `stage_decision` (text): Stage decision details
- `stage_analytics` (jsonb): Analytics data for stages
- `detected_stage` (text): Auto-detected stage
- `lead_type` (text): Type of lead

### Assignment & Ownership
- `producer_assigned` (text): Assigned producer
- `manual_producer_assigned` (text): Manually assigned producer
- `intake_assigned` (text): Assigned intake person
- `tatch_producer` (integer): Tatch producer ID
- `submission_person` (enum): Person handling submission

### Pending Actions
- `pending_action` (text): Next pending action
- `pending_actor_type` (text): Type of actor for pending action
- `pending_actor_name` (text): Name of pending actor
- `pending_actor_details` (text): Details about pending actor
- `pending_action_date_time` (timestamp): When pending action is due

### Flags & Indicators
- `dead_lead` (boolean): Whether lead is dead
- `duplicate_main_id` (bigint): Main ID if duplicate
- `follow_up_manual` (boolean): Manual follow-up flag
- `enrolled_outreach_ai` (boolean): Enrolled in AI outreach
- `flags` (enum): Various flags
- `priority` (enum): Priority level
- `remarket` (boolean): Remarketing flag
- `remarket_assigned` (text): Remarket assignment

### Quality Assurance
- `qa_status` (enum): QA status
- `qa_notes` (text): QA notes
- `qa_assigned` (text): QA assignment
- `qc_checked` (boolean): QC checked flag
- `sub_checked` (boolean): Sub checked flag
- `pitched_checked` (boolean): Pitched checked flag

### Notes
- `tivly_notes` (text): Tivly system notes
- `dakotah_notes` (text): Dakotah's notes
- `shabaig_notes` (text): Shabaig's notes
- `intake_notes` (jsonb): Intake notes
- `customer_context` (text): Customer context information

### Integration IDs
- `hubspot_record_id` (text): HubSpot record ID
- `intercom_id` (text): Intercom ID
- `slack_channel_id` (text): Slack channel ID
- `slack_channel_status` (enum): Slack channel status

### Lead Source
- `tivly_lead_id` (integer): Tivly lead ID
- `tivly_lead_acquisition_channel` (text): How lead was acquired
- `tivly_lead_cost` (numeric): Cost to acquire lead
- `tivly_campaign` (text): Campaign source
- `tivly_entry_date_time` (timestamp): When lead entered system
- `tivly_call_transferred_to` (text): Call transfer details
- `tivly_data` (jsonb): Additional Tivly data
- `best_time_to_contact` (text): Best time to reach prospect

### Metadata
- `created_at` (timestamp): When record was created
- `updated_at` (timestamp): When record was last updated
- `last_event_updated_at` (timestamp): Last event update
- `event_counter` (bigint): Event counter
- `zep_sync_status` (enum): Zep sync status
- `posthog_events_synced` (boolean): PostHog sync status
- `last_post_hog_sync_at` (timestamp): Last PostHog sync

### Miscellaneous
- `company_questionnaire` (text): General questionnaire
- `is_testing_user` (boolean): Whether this is a test account
- `number_of_upsell` (integer): Number of upsells

## Query Guidelines:

### ALWAYS Required:
- Filter by `id = {company_id}` in WHERE clause (security requirement)

### Common Query Patterns:

**Contact Details:**
```sql
SELECT
    company_name,
    company_primary_email,
    company_primary_phone,
    company_website,
    company_street_address_1,
    company_street_address_2,
    company_city,
    company_state,
    company_postal_code
FROM public.companies
WHERE id = {company_id}
```

**Business Profile:**
```sql
SELECT
    company_name,
    company_industry,
    company_sub_industry,
    company_annual_revenue_usd,
    company_full_time_employees,
    company_part_time_employees,
    company_years_in_business,
    company_description
FROM public.companies
WHERE id = {company_id}
```

**Insurance & Quote Info:**
```sql
SELECT
    company_name,
    bold_penguin_quote_id,
    insurance_types,
    instant_quote,
    submissions_kanban_status,
    renewal_active
FROM public.companies
WHERE id = {company_id}
```

## Important Notes:
- This table contains ONE row per company with MASTER DATA only
- This table does NOT contain quote pricing, amounts, or pricing breakdowns
- `bold_penguin_quote_id` is just an ID string, NOT the actual quote with pricing
- **For quote pricing/amounts**: Query communications.emails_silver table (NOT this table)
- **For communication history** (emails, calls): Query communications schema tables (NOT this table)
- JSONB columns (insurance_types, intake_notes, etc.) can be queried: `column_name->>'key'`
- Employee counts split into: company_full_time_employees + company_part_time_employees

## When to Use This Table:
✅ Company profile information (name, industry, employees)
✅ Contact information (email, phone, address)
✅ Business metrics (revenue, years in business)
✅ Insurance status (Bold Penguin quote ID)

❌ NOT for quote pricing/amounts - use communications.emails_silver
❌ NOT for email/communication history - use communications.emails_silver
❌ NOT for call records - use communications.phone_call_silver
"""

    @staticmethod
    def format_response(results: list, sql: str) -> str:
        """Format company data response."""
        if not results:
            return "No company information found."

        company = results[0]
        response = f"**{company.get('company_name', 'Company')}**\n\n"

        # Add available fields
        if 'company_primary_email' in company:
            response += f"📧 Email: {company['company_primary_email']}\n"
        if 'company_primary_phone' in company:
            response += f"📞 Phone: {company['company_primary_phone']}\n"
        if 'company_industry' in company:
            response += f"🏢 Industry: {company['company_industry']}\n"
        if 'company_full_time_employees' in company or 'company_part_time_employees' in company:
            ft = company.get('company_full_time_employees', 0) or 0
            pt = company.get('company_part_time_employees', 0) or 0
            total = ft + pt
            response += f"👥 Employees: {total} ({ft} FT, {pt} PT)\n"

        return response