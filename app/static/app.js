/*
  Reviewer Experience — hash SPA over the /api/close view model.

  Three seats, one close object (RACI):
  - accountant → Lines / Cases — prepare lineage; cannot Decide
  - fund_admin → Overview + Decide Cases + Export
  - fund_manager → material queue → Approve / Override

  Surface vocabulary is exactly Rule / Decision / Override / Unresolved and is
  derived server-side (display_method). Drafted candidates are shown as a
  list the reviewer picks from; they are never a Method.
*/

const REVIEWER = "Kenbun";
const SEVERITY_ORDER = { high: 0, medium: 1, low: 2 };
const ROLES = [
  { id: "accountant", labelKey: "role_accountant" },
  { id: "fund_admin", labelKey: "role_fund_admin" },
  { id: "fund_manager", labelKey: "role_fund_manager" },
];
const ASSIGN_OPTIONS = ["", "Kenbun", "Accountant", "Fund Admin"];
const MIN_REASON_LEN = 20;
const PROV_ICON = {
  Rule: "⚙",
  Decision: "✎",
  Override: "↺",
  Unresolved: "!",
};

/* ── Bilingual copy for non-technical reviewers (EN default / 中文) ── */
const I18N = {
  en: {
    loading: "Loading close…",
    load_error: "Could not load close data. Run ingest and start the server.",
    nav_overview: "Overview",
    nav_control: "Close control",
    nav_queue: "Queue",
    nav_cases: "Cases",
    nav_history: "History",
    nav_lines: "Lines",
    role_label: "Role",
    role_accountant: "Accountant",
    role_fund_admin: "Fund Admin",
    role_fund_manager: "Fund Manager",
    role_hint_accountant: "Prepare only — cannot Decide or Sign off",
    role_hint_fund_admin: "Decide Cases · Sign off · Export",
    role_hint_fund_manager: "Approve material exceptions · Sign off",
    guide_btn: "Workflow Guide",
    lang_en: "EN",
    lang_zh: "中文",
    back: "← Back",
    back_overview: "← Overview",
    status: "Status",
    tie_out: "Tie-out",
    financial_lines: "Financial Lines",
    auto_resolved: "Auto-resolved",
    needs_review: "Needs Review",
    tip_financial_lines:
      "Standardised financial lines parsed from bank statements or the general ledger. Each line is one amount you can trace to a source excerpt.",
    tip_auto_resolved:
      "Lines matched by an exact Rule (versioned mapping). No guesswork — only a full Rule hit counts as auto-resolved.",
    tip_needs_review:
      "Lines with no exact Rule. They become Cases and stay Unresolved until a person records a Decision.",
    tip_tie_out:
      "Batch check that amounts reconcile to the source total. PASS means difference is zero. FAIL blocks sign-off and export.",
    tip_severity:
      "High = material amount or compliance-sensitive. Fund Managers usually start with High. Medium can wait if High is clear.",
    tip_blockers:
      "Open work that still blocks a clean close. Click a tile to jump into the matching Case queue.",
    tip_control_checks:
      "Automated control gates for this batch (tie-out, open Cases, required tasks). All should be green before Sign off.",
    tip_signoff:
      "Sign-off freezes the batch after every Case is resolved and tie-out is PASS. Only then can you download the validated mapping CSV. This product does not write back to your system of record.",
    tip_source:
      "Evidence from the PDF or workbook for this line. Open the excerpt to see the matched narrative — amounts are never rounded.",
    tip_how_produced:
      "The production chain: Source → Line → Rule or Mapping gap → Case → Decision → Export. Shows whether a Rule or a person produced the classification.",
    tip_decision:
      "Accept keeps the proposal (or a drafted candidate). Override changes the treatment and requires a written reason (≥20 characters) for audit. Reject keeps the Case Unresolved.",
    tip_candidates:
      "Optional draft treatments grounded on the source excerpt, matching rules and prior decisions. They are never a Rule or a Decision until you Accept or Override.",
    tip_workbook_proposal:
      "A suggestion from the working file — not a posted fact. Accept or Override to record a Decision.",
    blockers: "Blockers",
    open_cases: "Open cases",
    unassigned: "Unassigned",
    high_severity: "High severity",
    unresolved_residue: "{n} Unresolved · the residue no map covers",
    unresolved_hint:
      "Each row is a Case with source lineage. Nothing here has been posted or guessed.",
    review_cases: "Review Cases →",
    control_checks: "Control checks",
    difference: "Difference",
    batch_signoff: "Batch sign-off",
    signed_off_banner: "This close is signed off",
    product_boundary:
      "Product boundary: validated mapping CSV — not an SoR API write-back.",
    download_export: "Download validated export",
    view_history: "View decision history",
    export_profile: "Profile: {profile}",
    export_blocked: "Export blocked",
    signoff_ready_hint:
      "All open cases are resolved and tie-out is PASS. Sign off unlocks validated export.",
    signoff_blocked_hint:
      "Available when open cases are 0 and tie-out is PASS.",
    sign_off_batch: "Sign off batch",
    export_unlocks: "Export unlocks after sign-off ({profile}).",
    close_control_title: "Close control",
    close_control_sub:
      "Dependencies and control gates for this shared close object.",
    ready_signoff: "Ready for sign-off",
    signoff_blocked: "Sign-off blocked",
    tasks_complete: "{done} / {total} tasks complete",
    required_gates: "Required gates: {list}",
    all_gates: "All required gates complete",
    blocking_cases: "Blocking cases",
    none: "None",
    task_complete: "Complete",
    task_ready: "Ready",
    task_blocked: "Blocked",
    task_not_started: "Not started",
    lines_title: "Lines",
    lines_sub: "Canonical financial lines for this close.",
    open_case: "Open case",
    validated_ready: "Validated / ready for export",
    queue_title_admin: "Case queue",
    queue_title_accountant: "My Cases",
    queue_title_manager: "Material review",
    shown_open: "{shown} shown · {open} open",
    tab_open: "Open ({n})",
    tab_resolved: "Resolved ({n})",
    filter_severity: "Severity",
    filter_reason: "Reason",
    all: "All",
    all_reasons: "All reasons",
    high: "High",
    medium: "Medium",
    no_cases: "No cases match these filters.",
    owner: "Owner",
    unassigned_opt: "Unassigned",
    candidates_drafted: "{n} candidates drafted",
    review: "Review",
    prepare: "Prepare",
    case_not_found: "Case not found.",
    back_to_queue: "Back to queue",
    source: "Source",
    document: "Document",
    location: "Location",
    amount: "Amount",
    description: "Description",
    view_source: "View source",
    how_produced: "How produced",
    provenance: "Provenance",
    workbook_proposal: "Workbook proposal",
    not_a_fact: "(not a fact)",
    source_match: "Source match",
    why_case: "Why is this a Case?",
    hide_why: "Hide Why",
    control: "Control",
    recon_category: "Reconciling category",
    materiality: "Materiality",
    control_ownership: "Control ownership",
    preparer: "Preparer",
    reviewer: "Reviewer",
    clearance_target: "Clearance target",
    decision: "Decision",
    recorded: "recorded",
    by: "By",
    chosen: "Chosen",
    final: "Final",
    view_case_history: "View decision history",
    prepare_only: "Prepare only",
    prepare_only_body:
      "Accountant files and prepares the Case. Fund Admin decides; Fund Manager approves material exceptions.",
    switch_to_decide: "Switch role to Fund Admin to record a Decision.",
    rejected_banner: "Rejected — still Unresolved",
    accepts: "Accepts",
    approves: "Approves",
    accept: "Accept",
    approve: "Approve",
    override: "Override",
    reject: "Reject",
    reject_admin_only: "Reject is Admin-only.",
    override_reason: "Override reason",
    reject_reason: "Reject reason",
    reason_required: "required · ≥ {n} characters",
    override_placeholder:
      "Why is the proposal wrong? This becomes part of the decision record.",
    reject_placeholder: "Why send this back / keep Unresolved?",
    final_classification: "Final classification",
    final_account: "Final account",
    final_project: "Final project code",
    commit_override: "Commit override",
    confirm_reject: "Confirm reject",
    cancel: "Cancel",
    reason_hint_example:
      "Example: Classification should be Management fee, not Bank charge — fee schedule clause 4.2 applies to this counterparty.",
    chars_need: "{cur} / {min} characters · need {left} more",
    chars_ok: "{cur} / {min} characters · ready",
    candidates: "Candidates",
    candidates_footer:
      "Drafted {at}{model}. Not a Rule, not a Decision. Accept or Override to record.",
    draft_candidates: "Draft candidates",
    redraft_candidates: "Redraft candidates",
    draft_hint:
      "Grounded on the source excerpt, matching rules and prior decisions. Every candidate cites its evidence.",
    draft_off: "Candidate drafting off — set GOOGLE_API_KEY in .env.",
    history_title: "Decision history",
    history_sub: "Every Accept, Override, Reject and batch sign-off for this close.",
    case_timeline: "Case timeline",
    open_case_btn: "Open case",
    case_timeline_btn: "Case timeline",
    all_decisions: "← All decisions",
    resolved_queue: "Resolved queue",
    action_sign_off: "Batch sign-off",
    action_accept: "Decision",
    action_override: "Override",
    action_reject: "Rejected · Unresolved",
    footer:
      "Rule · Decision · Override · Unresolved. Accountant prepares · Admin decides · Manager approves. Export after sign-off.",
    footer_role: "Role",
    footer_drafts_on: "candidate drafts on ({model})",
    footer_drafts_off: "candidate drafts off",
    chain_source: "Source",
    chain_line: "Line",
    chain_rule: "Rule",
    chain_gap: "Mapping gap",
    chain_case: "Case",
    chain_decision: "Decision",
    chain_export: "Export",
    chain_open: "Open — needs human Decision",
    chain_closed: "Closed by Decision",
    chain_not_recorded: "Not recorded",
    chain_export_ready: "Validated export ready",
    chain_export_signed: "Signed off — check export blockers",
    chain_export_after: "After batch sign-off",
    chain_rule_applied: "{id} applied",
    chain_no_rule: "No complete exact Rule",
    guide_title: "Workflow Guide",
    guide_close: "Close",
    guide_intro:
      "This control layer sits between source files and your system of record. It never auto-posts. Use the four provenance words below — they mean the same thing everywhere.",
    guide_steps_title: "Five steps to a validated export",
    guide_step1_t: "1. Source → Lines",
    guide_step1_d:
      "Bank PDFs or GL extracts become canonical financial Lines. Every amount stays traceable to a source excerpt.",
    guide_step2_t: "2. Rule or Mapping gap",
    guide_step2_d:
      "Only an exact Rule hit auto-resolves. Anything else becomes an open Case (Unresolved) — never a silent guess.",
    guide_step3_t: "3. Human Decision",
    guide_step3_d:
      "Accountant prepares. Fund Admin Accepts, Overrides (with reason), or Rejects. Fund Manager Approves material items.",
    guide_step4_t: "4. Tie-out gate",
    guide_step4_d:
      "Batch totals must reconcile (difference = 0). FAIL blocks sign-off until the residue is explained.",
    guide_step5_t: "5. Sign-off → Export",
    guide_step5_d:
      "After zero open Cases and PASS tie-out, Sign off unlocks a downloadable validated mapping CSV. No SoR API write-back.",
    guide_raci_title: "Who can do what",
    guide_raci_accountant:
      "Accountant — Prepare: attach lineage, draft candidates, file Cases. Cannot Accept, Override, Reject, or Sign off.",
    guide_raci_admin:
      "Fund Admin — Decide: Accept / Reject / Override Cases, coordinate the queue, Sign off, download export.",
    guide_raci_manager:
      "Fund Manager — Approve material exceptions (Accept / Override). Can Sign off. Cannot Reject.",
    guide_prov_title: "Four provenance words",
    guide_prov_rule:
      "Rule — Produced by a versioned mapping the accountant owns. Exact match only.",
    guide_prov_decision:
      "Decision — A person chose a treatment and wrote (or accepted) a reason. Audit trail included.",
    guide_prov_override:
      "Override — A reviewer changed a Rule or Decision and recorded why (≥20 characters).",
    guide_prov_unresolved:
      "Unresolved — No Rule matched and no Decision yet. Safe residue — never posted automatically.",
    guide_faq_title: "Common questions",
    guide_faq1_q: "Why is Download export greyed out?",
    guide_faq1_a:
      "You need: every Case resolved, tie-out PASS, then batch Sign off. Until then the button stays disabled and blockers list the reason.",
    guide_faq2_q: "Why must Override / Reject reasons be ≥20 characters?",
    guide_faq2_a:
      "Audit and dual-control: reviewers must leave a clear business rationale on the decision record, not a one-word note.",
    guide_faq3_q: "What are Candidates?",
    guide_faq3_a:
      "Optional draft treatments grounded on the source excerpt, matching rules and prior decisions. They never become a Rule or Decision until you Accept or Override.",
    guide_faq4_q: "Wrong role and buttons look disabled?",
    guide_faq4_a:
      "Use the Role switcher in the top bar. The hint next to it shows what your current seat can do. Open this Guide anytime.",
  },
  zh: {
    loading: "正在加载关账数据…",
    load_error: "无法加载关账数据。请先完成 ingest 并启动服务。",
    nav_overview: "总览",
    nav_control: "关账控制",
    nav_queue: "待办队列",
    nav_cases: "案件",
    nav_history: "历史",
    nav_lines: "分录",
    role_label: "角色",
    role_accountant: "基金会计",
    role_fund_admin: "基金主管",
    role_fund_manager: "基金经理",
    role_hint_accountant: "仅编制 — 不可裁决或签署",
    role_hint_fund_admin: "裁决案件 · 签署 · 导出",
    role_hint_fund_manager: "审批重大例外 · 可签署",
    guide_btn: "业务指引",
    lang_en: "EN",
    lang_zh: "中文",
    back: "← 返回",
    back_overview: "← 总览",
    status: "状态",
    tie_out: "轧账",
    financial_lines: "财务分录",
    auto_resolved: "自动匹配",
    needs_review: "待复核",
    tip_financial_lines:
      "从银行对账单或总账解析出的标准化财务分录。每一笔金额都可以一键追溯到原始摘录。",
    tip_auto_resolved:
      "由完整精确规则（带版本的映射）直接匹配的分录。只有规则全命中才算自动匹配，不做模糊猜测。",
    tip_needs_review:
      "没有命中精确规则的分录，会变成案件并保持「未决」，直到人工记录决议。",
    tip_tie_out:
      "批次金额与来源合计是否轧平。PASS 表示差额为 0；FAIL 会阻断签署与导出。",
    tip_severity:
      "High = 重大金额或合规敏感项，基金经理通常优先处理。Medium 可在 High 清空后再看。",
    tip_blockers:
      "仍会阻碍干净关账的未完成项。点击卡片可跳到对应案件队列。",
    tip_control_checks:
      "本批次的自动控制门（轧账、未决案件、必做任务）。签署前应全部通过。",
    tip_signoff:
      "全部案件已决且轧账 PASS 后，签署会冻结本批次，然后才能下载已校验映射 CSV。本产品不会回写会计系统。",
    tip_source:
      "本分录对应的 PDF / 工作簿证据。打开摘录可查看匹配叙述；金额绝不四舍五入。",
    tip_how_produced:
      "生产链路：来源 → 分录 → 规则或缺映射 → 案件 → 决议 → 导出。一眼看出分类来自规则还是人工。",
    tip_decision:
      "Accept 接受提案（或候选方案）。Override 改写处理并须写明理由（≥20 字）备审计。Reject 保持未决。",
    tip_candidates:
      "可选的草案处理，依据来源摘录、匹配规则与历史决议归纳。在您 Accept / Override 之前，它们既不是规则也不是决议。",
    tip_workbook_proposal:
      "来自工作簿的建议，不是已入账事实。Accept 或 Override 才会记成决议。",
    blockers: "阻断项",
    open_cases: "未决案件",
    unassigned: "未分派",
    high_severity: "高严重度",
    unresolved_residue: "{n} 未决 · 映射未覆盖的残差",
    unresolved_hint:
      "每一行都是带来源血缘的案件。此处没有任何已入账或盲目猜测的结果。",
    review_cases: "复核案件 →",
    control_checks: "控制检查",
    difference: "差额",
    batch_signoff: "批次签署",
    signed_off_banner: "本关账批次已签署",
    product_boundary: "产品边界：已校验映射 CSV — 非会计系统 API 回写。",
    download_export: "下载已校验导出",
    view_history: "查看决议历史",
    export_profile: "配置文件：{profile}",
    export_blocked: "导出已阻断",
    signoff_ready_hint:
      "未决案件为 0 且轧账 PASS。签署后即可下载已校验导出。",
    signoff_blocked_hint: "需未决案件为 0 且轧账 PASS 后方可用。",
    sign_off_batch: "签署本批次",
    export_unlocks: "签署后解锁导出（{profile}）。",
    close_control_title: "关账控制",
    close_control_sub: "本共享关账对象的依赖与控制门。",
    ready_signoff: "可签署",
    signoff_blocked: "签署已阻断",
    tasks_complete: "已完成 {done} / {total} 项任务",
    required_gates: "必做门控：{list}",
    all_gates: "全部必做门控已完成",
    blocking_cases: "阻断案件",
    none: "无",
    task_complete: "完成",
    task_ready: "就绪",
    task_blocked: "阻断",
    task_not_started: "未开始",
    lines_title: "分录",
    lines_sub: "本关账的标准财务分录。",
    open_case: "未决案件",
    validated_ready: "已校验 / 可导出",
    queue_title_admin: "案件队列",
    queue_title_accountant: "我的案件",
    queue_title_manager: "重大复核",
    shown_open: "显示 {shown} · 未决 {open}",
    tab_open: "未决 ({n})",
    tab_resolved: "已决 ({n})",
    filter_severity: "严重度",
    filter_reason: "原因",
    all: "全部",
    all_reasons: "全部原因",
    high: "高",
    medium: "中",
    no_cases: "没有符合筛选条件的案件。",
    owner: "负责人",
    unassigned_opt: "未分派",
    candidates_drafted: "已起草 {n} 个候选",
    review: "复核",
    prepare: "编制",
    case_not_found: "未找到案件。",
    back_to_queue: "返回队列",
    source: "来源",
    document: "单据",
    location: "位置",
    amount: "金额",
    description: "说明",
    view_source: "查看来源",
    how_produced: "如何生成",
    provenance: "出处",
    workbook_proposal: "工作簿提案",
    not_a_fact: "（非既成事实）",
    source_match: "来源匹配",
    why_case: "为何成为案件？",
    hide_why: "收起原因",
    control: "控制",
    recon_category: "对账类别",
    materiality: "重要性",
    control_ownership: "控制职责",
    preparer: "编制人",
    reviewer: "复核人",
    clearance_target: "清账目标",
    decision: "决议",
    recorded: "已记录",
    by: "由",
    chosen: "选用",
    final: "最终",
    view_case_history: "查看决议历史",
    prepare_only: "仅编制",
    prepare_only_body:
      "会计负责建档与编制案件。基金主管裁决；基金经理审批重大例外。",
    switch_to_decide: "请切换到「基金主管」角色以记录决议。",
    rejected_banner: "已驳回 — 仍为未决",
    accepts: "接受",
    approves: "批准",
    accept: "接受",
    approve: "批准",
    override: "调整",
    reject: "驳回",
    reject_admin_only: "驳回仅基金主管可用。",
    override_reason: "调整理由",
    reject_reason: "驳回理由",
    reason_required: "必填 · ≥ {n} 字符",
    override_placeholder: "为何提案不正确？此内容将写入决议记录。",
    reject_placeholder: "为何退回 / 保持未决？",
    final_classification: "最终分类",
    final_account: "最终科目",
    final_project: "最终项目代码",
    commit_override: "提交调整",
    confirm_reject: "确认驳回",
    cancel: "取消",
    reason_hint_example:
      "示例：分类应为管理费而非银行手续费 — 费用表 4.2 条适用于该对手方。",
    chars_need: "{cur} / {min} 字符 · 还需 {left}",
    chars_ok: "{cur} / {min} 字符 · 已达标",
    candidates: "候选方案",
    candidates_footer:
      "起草于 {at}{model}。不是规则，也不是决议。Accept 或 Override 才会入账记录。",
    draft_candidates: "起草候选",
    redraft_candidates: "重新起草",
    draft_hint:
      "依据来源摘录、匹配规则与历史决议。每个候选都会标注证据。",
    draft_off: "候选起草未启用 — 请在 .env 设置 GOOGLE_API_KEY。",
    history_title: "决议历史",
    history_sub: "本关账全部 Accept、Override、Reject 与批次签署记录。",
    case_timeline: "案件时间线",
    open_case_btn: "打开案件",
    case_timeline_btn: "案件时间线",
    all_decisions: "← 全部决议",
    resolved_queue: "已决队列",
    action_sign_off: "批次签署",
    action_accept: "决议",
    action_override: "调整",
    action_reject: "已驳回 · 未决",
    footer:
      "规则 · 决议 · 调整 · 未决。会计编制 · 主管裁决 · 经理审批。签署后导出。",
    footer_role: "角色",
    footer_drafts_on: "候选起草已开（{model}）",
    footer_drafts_off: "候选起草关闭",
    chain_source: "来源",
    chain_line: "分录",
    chain_rule: "规则",
    chain_gap: "映射缺口",
    chain_case: "案件",
    chain_decision: "决议",
    chain_export: "导出",
    chain_open: "未决 — 需人工决议",
    chain_closed: "已由决议关闭",
    chain_not_recorded: "尚未记录",
    chain_export_ready: "已校验导出可用",
    chain_export_signed: "已签署 — 请检查导出阻断项",
    chain_export_after: "批次签署之后",
    chain_rule_applied: "已应用 {id}",
    chain_no_rule: "无完整精确规则",
    guide_title: "业务指引",
    guide_close: "关闭",
    guide_intro:
      "本控制层位于原始凭证与会计系统之间，从不自动入账。请始终使用下方四个出处用语 — 界面各处含义一致。",
    guide_steps_title: "五步完成已校验导出",
    guide_step1_t: "1. 来源 → 分录",
    guide_step1_d:
      "银行 PDF 或总账抽取成为标准财务分录。每笔金额均可追溯到来源摘录。",
    guide_step2_t: "2. 规则或映射缺口",
    guide_step2_d:
      "只有精确规则命中才会自动匹配。其余一律进入未决案件，绝无静默猜测。",
    guide_step3_t: "3. 人工决议",
    guide_step3_d:
      "会计编制。基金主管 Accept / Override（须理由）/ Reject。基金经理审批重大项。",
    guide_step4_t: "4. 轧账门控",
    guide_step4_d:
      "批次合计必须轧平（差额 = 0）。FAIL 会阻断签署，直至残差说明清楚。",
    guide_step5_t: "5. 签署 → 导出",
    guide_step5_d:
      "未决案件归零且轧账 PASS 后，签署解锁可下载的已校验映射 CSV。不做会计系统 API 回写。",
    guide_raci_title: "谁能做什么",
    guide_raci_accountant:
      "基金会计 — 编制：补充血缘、起草候选、建档案件。不可 Accept / Override / Reject / 签署。",
    guide_raci_admin:
      "基金主管 — 裁决：Accept / Reject / Override、协调队列、签署、下载导出。",
    guide_raci_manager:
      "基金经理 — 审批重大例外（Accept / Override）。可签署。不可 Reject。",
    guide_prov_title: "四个出处用语",
    guide_prov_rule: "Rule（规则）— 由会计维护的带版本映射精确命中产生。",
    guide_prov_decision:
      "Decision（决议）— 人工选定处理并留下（或接受）理由，含审计轨迹。",
    guide_prov_override:
      "Override（调整）— 复核人改写规则或决议结果，并记录原因（≥20 字符）。",
    guide_prov_unresolved:
      "Unresolved（未决）— 无规则命中且尚无决议。安全残差，绝不自动入账。",
    guide_faq_title: "常见问题",
    guide_faq1_q: "为什么「下载导出」是灰色的？",
    guide_faq1_a:
      "需要：全部案件已决 + 轧账 PASS + 完成批次签署。否则按钮保持禁用，阻断列表会说明原因。",
    guide_faq2_q: "为什么 Override / Reject 理由要 ≥20 字符？",
    guide_faq2_a:
      "审计与双重控制要求：复核人必须在决议记录中留下清楚的业务依据，不能只写一两个字。",
    guide_faq3_q: "候选方案是什么？",
    guide_faq3_a:
      "可选草案，依据来源摘录、匹配规则与历史决议。在您 Accept 或 Override 之前，它们不会变成规则或决议。",
    guide_faq4_q: "角色选错导致按钮不可用？",
    guide_faq4_a:
      "使用顶栏「角色」切换。旁边的提示说明当前席位能做什么。可随时打开本业务指引。",
  },
};

let state = {
  payload: null,
  role: localStorage.getItem("ylookup_role") || "fund_admin",
  lang: localStorage.getItem("ylookup_lang") || "en",
  guideOpen: false,
  route: { name: "overview", params: {}, query: {} },
  queueTab: "open",
  filterSeverity: "all",
  filterReason: "all",
  whyOpen: {},
  overrideMode: {},
  rejectMode: {},
  selectedCandidate: {},
  flash: null,
};

function t(key, vars) {
  const dict = I18N[state.lang] || I18N.en;
  let s = dict[key];
  if (s === undefined) s = I18N.en[key];
  if (s === undefined) return key;
  if (vars) {
    Object.keys(vars).forEach((k) => {
      s = s.replace(new RegExp(`\\{${k}\\}`, "g"), String(vars[k]));
    });
  }
  return s;
}

function tip(key) {
  const text = t(key);
  return `<button type="button" class="tip-btn" tabindex="0" aria-label="${esc(
    text
  )}" data-tip="${esc(text)}">?</button>`;
}

function setLang(lang) {
  state.lang = lang === "zh" ? "zh" : "en";
  localStorage.setItem("ylookup_lang", state.lang);
  render();
}

function roleHint() {
  if (state.role === "accountant") return t("role_hint_accountant");
  if (state.role === "fund_manager") return t("role_hint_fund_manager");
  return t("role_hint_fund_admin");
}

function reasonCounterHtml(inputId) {
  return `<p class="reason-counter muted small" data-reason-for="${esc(
    inputId
  )}" aria-live="polite"></p>
    <p class="muted small reason-example">${esc(t("reason_hint_example"))}</p>`;
}

function updateReasonCounters() {
  document.querySelectorAll("[data-reason-for]").forEach((el) => {
    const id = el.getAttribute("data-reason-for");
    const input = document.getElementById(id);
    if (!input) return;
    const cur = (input.value || "").trim().length;
    const left = Math.max(0, MIN_REASON_LEN - cur);
    const ok = cur >= MIN_REASON_LEN;
    el.textContent = ok
      ? t("chars_ok", { cur, min: MIN_REASON_LEN })
      : t("chars_need", { cur, min: MIN_REASON_LEN, left });
    el.classList.toggle("reason-ok", ok);
    el.classList.toggle("reason-need", !ok);
  });
}

const fmt = (n, ccy) => {
  const code = ccy || "EUR";
  const num = new Intl.NumberFormat("en-GB", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(n) || 0);
  return `${num} ${code}`;
};

const fmtDiff = (n, ccy) => {
  const code = ccy || "EUR";
  const num = new Intl.NumberFormat("en-GB", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Math.abs(Number(n) || 0));
  return `${num} ${code}`;
};

function fmtDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) {
    // Already a date-only string like 2026-08-04
    const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(iso));
    if (!m) return String(iso);
    const months = [
      "Jan",
      "Feb",
      "Mar",
      "Apr",
      "May",
      "Jun",
      "Jul",
      "Aug",
      "Sep",
      "Oct",
      "Nov",
      "Dec",
    ];
    return `${Number(m[3])} ${months[Number(m[2]) - 1]} ${m[1]}`;
  }
  const months = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
  ];
  return `${d.getUTCDate()} ${months[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
}

function esc(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function roleHome(role) {
  if (role === "accountant") return "#/lines";
  if (role === "fund_manager") return "#/queue";
  return "#/overview";
}

function canDecideCase() {
  return state.role === "fund_admin" || state.role === "fund_manager";
}

function canRejectCase() {
  return state.role === "fund_admin";
}

function acceptLabel() {
  return state.role === "fund_manager" ? t("approve") : t("accept");
}

// The one word the reviewer sees. Server-derived; the rule id is only
// appended when the word is Rule (a partial hit is shown separately).
function methodBadge(displayMethod, ruleId) {
  const label = displayMethod || "Unresolved";
  const cls = String(label).toLowerCase().replace(/\s+/g, "-");
  const icon = PROV_ICON[label] || "";
  const rule = label === "Rule" && ruleId ? ` · ${esc(ruleId)}` : "";
  return `<span class="method-badge method-${esc(cls)}" aria-label="Provenance: ${esc(
    label
  )}${ruleId ? `, ${esc(ruleId)}` : ""}"><span class="prov-icon" aria-hidden="true">${icon}</span> ${esc(
    label
  )}${rule}</span>`;
}

function partialHint(label) {
  return label ? `<span class="partial-hint">${esc(label)}</span>` : "";
}

function lineStatusText(status) {
  if (status === "open") return t("open_case");
  if (status === "accepted" || status === "resolved") return t("validated_ready");
  return status || "";
}

function parseHash() {
  const raw = (location.hash || "").replace(/^#/, "");
  const fallback =
    state.role === "accountant"
      ? "/lines"
      : state.role === "fund_manager"
        ? "/queue"
        : "/overview";
  const effective = raw || fallback;
  const [pathPart, queryPart] = effective.split("?");
  const parts = pathPart.split("/").filter(Boolean);
  const query = {};
  if (queryPart) {
    queryPart.split("&").forEach((pair) => {
      const [k, v] = pair.split("=");
      if (k) query[decodeURIComponent(k)] = decodeURIComponent(v || "");
    });
  }
  if (parts[0] === "lines") {
    return { name: "lines", params: {}, query };
  }
  if (parts[0] === "queue") {
    return { name: "queue", params: {}, query };
  }
  if (parts[0] === "control") {
    return { name: "control", params: {}, query };
  }
  if (parts[0] === "case" && parts[1]) {
    return { name: "case", params: { id: parts[1] }, query };
  }
  if (parts[0] === "history") {
    if (parts[1]) {
      return { name: "case-history", params: { id: parts[1] }, query };
    }
    return { name: "history", params: {}, query };
  }
  return { name: "overview", params: {}, query };
}

function navigate(hash, { keepFlash = false } = {}) {
  if (!keepFlash) state.flash = null;
  location.hash = hash.startsWith("#") ? hash : `#${hash}`;
}

function findCase(id) {
  return (state.payload?.cases || []).find((c) => c.case_id === id);
}

function currency() {
  return state.payload?.batch?.currency || "EUR";
}

function canSignOff() {
  const o = state.payload?.overview;
  if (!o) return false;
  return (
    !o.signed_off &&
    o.signoff_ready === true
  );
}

function canExport() {
  const o = state.payload?.overview;
  if (!o) return false;
  return o.export_ready === true && o.signed_off === true;
}

function exportBlockersHtml() {
  const blockers = state.payload?.overview?.export_blockers || [];
  if (!blockers.length) return "";
  return `<ul class="export-blockers">${blockers
    .map((b) => `<li>${esc(b)}</li>`)
    .join("")}</ul>`;
}

function setRole(role) {
  state.role = role;
  localStorage.setItem("ylookup_role", role);
  if (role === "fund_manager") {
    state.filterSeverity = "high";
  } else if (role === "accountant") {
    state.filterSeverity = "all";
  }
  navigate(roleHome(role));
  render();
}

function renderTopNav() {
  const name = state.route.name;
  const historyActive = name === "history" || name === "case-history";
  const link = (hash, label, active) =>
    `<button type="button" class="nav-link ${active ? "active" : ""}" data-nav="${hash}">${label}</button>`;

  const roleLinks =
    state.role === "accountant"
      ? `${link("#/lines", t("nav_lines"), name === "lines")}
         ${link("#/queue", t("nav_cases"), name === "queue" || name === "case")}
         ${link("#/history", t("nav_history"), historyActive)}`
      : `${link("#/overview", t("nav_overview"), name === "overview")}
         ${link("#/control", t("nav_control"), name === "control")}
         ${link("#/queue", t("nav_queue"), name === "queue" || name === "case")}
         ${link("#/history", t("nav_history"), historyActive)}
         ${link("#/lines", t("nav_lines"), name === "lines")}`;

  const roleSelect = `
    <div class="role-cluster">
      <label class="role-switch">
        <span class="role-switch-label">${esc(t("role_label"))}</span>
        <select id="role-select">
          ${ROLES.map(
            (r) =>
              `<option value="${r.id}" ${state.role === r.id ? "selected" : ""}>${esc(
                t(r.labelKey)
              )}</option>`
          ).join("")}
        </select>
      </label>
      <span class="role-hint" title="${esc(roleHint())}">${esc(roleHint())}</span>
    </div>`;

  const langSwitch = `
    <div class="lang-switch" role="group" aria-label="Language">
      <button type="button" class="lang-btn ${state.lang === "en" ? "active" : ""}" data-lang="en">${esc(
        t("lang_en")
      )}</button>
      <button type="button" class="lang-btn ${state.lang === "zh" ? "active" : ""}" data-lang="zh">${esc(
        t("lang_zh")
      )}</button>
    </div>`;

  return `
    <nav class="topnav" aria-label="Reviewer">
      <div class="topnav-brand">
        <span class="topnav-mark">Close Control</span>
      </div>
      <div class="topnav-links">${roleLinks}</div>
      <div class="topnav-tools">
        <button type="button" class="guide-btn" data-open-guide>${esc(t("guide_btn"))}</button>
        ${langSwitch}
        ${roleSelect}
      </div>
    </nav>`;
}

function renderGuideModal() {
  if (!state.guideOpen) return "";
  return `
    <div class="guide-overlay" data-close-guide role="presentation">
      <div class="guide-modal" role="dialog" aria-modal="true" aria-labelledby="guide-title" tabindex="-1" data-guide-panel>
        <header class="guide-header">
          <h2 id="guide-title">${esc(t("guide_title"))}</h2>
          <button type="button" class="guide-close" data-close-guide aria-label="${esc(
            t("guide_close")
          )}">×</button>
        </header>
        <p class="guide-intro">${esc(t("guide_intro"))}</p>

        <section class="guide-section">
          <h3>${esc(t("guide_steps_title"))}</h3>
          <ol class="guide-steps">
            <li><strong>${esc(t("guide_step1_t"))}</strong><span>${esc(t("guide_step1_d"))}</span></li>
            <li><strong>${esc(t("guide_step2_t"))}</strong><span>${esc(t("guide_step2_d"))}</span></li>
            <li><strong>${esc(t("guide_step3_t"))}</strong><span>${esc(t("guide_step3_d"))}</span></li>
            <li><strong>${esc(t("guide_step4_t"))}</strong><span>${esc(t("guide_step4_d"))}</span></li>
            <li><strong>${esc(t("guide_step5_t"))}</strong><span>${esc(t("guide_step5_d"))}</span></li>
          </ol>
        </section>

        <section class="guide-section">
          <h3>${esc(t("guide_raci_title"))}</h3>
          <ul class="guide-list">
            <li>${esc(t("guide_raci_accountant"))}</li>
            <li>${esc(t("guide_raci_admin"))}</li>
            <li>${esc(t("guide_raci_manager"))}</li>
          </ul>
        </section>

        <section class="guide-section">
          <h3>${esc(t("guide_prov_title"))}</h3>
          <ul class="guide-prov">
            <li><span class="method-badge method-rule"><span class="prov-icon" aria-hidden="true">⚙</span> Rule</span> ${esc(
              t("guide_prov_rule")
            )}</li>
            <li><span class="method-badge method-decision"><span class="prov-icon" aria-hidden="true">✎</span> Decision</span> ${esc(
              t("guide_prov_decision")
            )}</li>
            <li><span class="method-badge method-override"><span class="prov-icon" aria-hidden="true">↺</span> Override</span> ${esc(
              t("guide_prov_override")
            )}</li>
            <li><span class="method-badge method-unresolved"><span class="prov-icon" aria-hidden="true">!</span> Unresolved</span> ${esc(
              t("guide_prov_unresolved")
            )}</li>
          </ul>
        </section>

        <section class="guide-section">
          <h3>${esc(t("guide_faq_title"))}</h3>
          <dl class="guide-faq">
            <dt>${esc(t("guide_faq1_q"))}</dt>
            <dd>${esc(t("guide_faq1_a"))}</dd>
            <dt>${esc(t("guide_faq2_q"))}</dt>
            <dd>${esc(t("guide_faq2_a"))}</dd>
            <dt>${esc(t("guide_faq3_q"))}</dt>
            <dd>${esc(t("guide_faq3_a"))}</dd>
            <dt>${esc(t("guide_faq4_q"))}</dt>
            <dd>${esc(t("guide_faq4_a"))}</dd>
          </dl>
        </section>
      </div>
    </div>`;
}

/* ───────── Overview ───────── */

function renderOverview() {
  const o = state.payload.overview;
  const ccy = currency();
  const blockers = o.blockers || {};
  const breakdown = (o.reason_breakdown || [])
    .map(
      (row) => `
      <button type="button" class="breakdown-row ${row.count ? "" : "zero"}" data-nav="#/queue?reason=${esc(row.category)}">
        <span class="breakdown-count">${row.count}</span>
        <span class="breakdown-label">${esc(row.label)}</span>
      </button>`
    )
    .join("");

  const checks = (o.control_checks || [])
    .map(
      (ch) => `
      <li class="${ch.ok ? "ok" : "bad"}">
        <span class="check-mark">${ch.ok ? "✓" : "✗"}</span>
        <div>
          <strong>${esc(ch.label)}</strong>
          <span class="muted">${esc(ch.detail)}</span>
        </div>
      </li>`
    )
    .join("");

  const statusClass =
    o.status === "Signed Off" || o.status === "Clean" ? "clean" : "review";
  const signOffEnabled = canSignOff();
  const exportEnabled = canExport();
  const profile = o.export_profile || "validated_mapping_csv_v1";
  let signOffBlock;
  if (o.signed_off) {
    signOffBlock = `
      <section class="signoff-card done">
        <h2>${esc(t("batch_signoff"))} ${tip("tip_signoff")}</h2>
        <p class="resolved-banner">${esc(t("signed_off_banner"))}</p>
        <p class="muted">${esc(t("product_boundary"))}</p>
        <div class="signoff-actions">
          <button type="button" class="primary" data-export ${
            exportEnabled ? "" : "disabled"
          }>${esc(t("download_export"))}</button>
          <button type="button" data-nav="#/history">${esc(t("view_history"))}</button>
        </div>
        ${
          exportEnabled
            ? `<p class="muted small">${esc(t("export_profile", { profile }))}</p>`
            : `<p class="muted small">${esc(t("export_blocked"))}</p>${exportBlockersHtml()}`
        }
      </section>`;
  } else if (state.role === "fund_admin" || state.role === "fund_manager") {
    const hint = signOffEnabled
      ? t("signoff_ready_hint")
      : t("signoff_blocked_hint");
    signOffBlock = `
      <section class="signoff-card">
        <h2>${esc(t("batch_signoff"))} ${tip("tip_signoff")}</h2>
        <p class="muted">${esc(hint)}</p>
        <div class="signoff-actions">
          <button type="button" class="primary" data-sign-off ${
            signOffEnabled ? "" : "disabled"
          }>${esc(t("sign_off_batch"))}</button>
          <button type="button" data-export disabled>${esc(t("download_export"))}</button>
        </div>
        <p class="muted small">${esc(t("export_unlocks", { profile }))}</p>
      </section>`;
  } else {
    signOffBlock = "";
  }

  const blockerCard =
    state.role === "fund_admin"
      ? `
    <section class="attention-card blockers-card">
      <h2>${esc(t("blockers"))} ${tip("tip_blockers")}</h2>
      <div class="blocker-grid">
        <button type="button" class="blocker-stat" data-nav="#/queue">
          <span class="stat-value accent">${Number(blockers.open_total || 0)}</span>
          <span class="stat-label">${esc(t("open_cases"))}</span>
        </button>
        <button type="button" class="blocker-stat" data-nav="#/queue?unassigned=1">
          <span class="stat-value accent">${Number(blockers.unassigned_open || 0)}</span>
          <span class="stat-label">${esc(t("unassigned"))}</span>
        </button>
        <button type="button" class="blocker-stat" data-nav="#/queue?severity=high">
          <span class="stat-value accent">${Number(blockers.high_open || 0)}</span>
          <span class="stat-label">${esc(t("high_severity"))}</span>
        </button>
      </div>
    </section>`
      : "";

  return `
    <header class="page-header">
      <div>
        <p class="eyebrow">Close Control Layer${
          o.workflow_label ? ` · ${esc(o.workflow_label)}` : ""
        }</p>
        <h1>${esc(o.period_label)}</h1>
        <p class="status-line">
          ${esc(t("status"))}:
          <span class="status-pill ${statusClass}">${esc(o.status)}</span>
        </p>
      </div>
      <div class="badge ${o.tie_out.status === "PASS" ? "pass" : "fail"}">
        ${esc(t("tie_out"))} ${esc(o.tie_out.status)}
      </div>
    </header>

    <section class="stat-grid" aria-label="Close summary">
      <div class="stat">
        <span class="stat-label">${esc(t("financial_lines"))} ${tip("tip_financial_lines")}</span>
        <span class="stat-value">${o.total_lines.toLocaleString()}</span>
      </div>
      <div class="stat">
        <span class="stat-label">${esc(t("auto_resolved"))} ${tip("tip_auto_resolved")}</span>
        <span class="stat-value">${o.auto_resolved.toLocaleString()}</span>
      </div>
      <div class="stat">
        <span class="stat-label">${esc(t("needs_review"))} ${tip("tip_needs_review")}</span>
        <span class="stat-value accent">${o.needs_review.toLocaleString()}</span>
      </div>
      <div class="stat">
        <span class="stat-label">${esc(t("tie_out"))} ${tip("tip_tie_out")}</span>
        <span class="stat-value ${o.tie_out.status === "PASS" ? "pass-text" : "fail-text"}">
          ${o.tie_out.status === "PASS" ? "✓ PASS" : "✗ FAIL"}
        </span>
      </div>
    </section>

    ${blockerCard}

    <section class="attention-card">
      <h2>${esc(t("unresolved_residue", { n: o.needs_review }))}</h2>
      <p class="muted small">${esc(t("unresolved_hint"))}</p>
      <div class="breakdown">${breakdown}</div>
      <button type="button" class="primary cta" data-nav="#/queue">${esc(t("review_cases"))}</button>
    </section>

    <section class="controls-card">
      <h2>${esc(t("control_checks"))} ${tip("tip_control_checks")}</h2>
      <ul class="check-list">${checks}</ul>
      <p class="muted small">${esc(t("difference"))}: ${fmtDiff(o.tie_out.difference, ccy)}</p>
    </section>

    ${signOffBlock}
  `;
}

/* ───────── Close control ───────── */

function taskLabel(status) {
  return {
    complete: t("task_complete"),
    in_progress: t("task_ready"),
    blocked: t("task_blocked"),
    not_started: t("task_not_started"),
  }[status] || status || t("task_not_started");
}

function renderCloseControl() {
  const o = state.payload.overview;
  const tasks = o.control_tasks || [];
  const rows = tasks
    .map((task) => {
      const blockers = task.blockers || [];
      const blockerLinks = blockers.length
        ? blockers
            .map(
              (id) =>
                `<button type="button" class="case-link" data-nav="#/case/${esc(id)}">${esc(id)}</button>`
            )
            .join("")
        : `<span class="muted small">${esc(t("none"))}</span>`;
      return `
        <article class="task-row task-${esc(task.status)}">
          <div class="task-main">
            <span class="task-status">${esc(taskLabel(task.status))}</span>
            <div>
              <h3>${esc(task.title)}</h3>
              <p class="muted small">Due ${esc(task.due_day)} · Owner: ${esc(task.owner)} · Reviewer: ${esc(task.reviewer)}</p>
              ${task.note ? `<p class="muted small">${esc(task.note)}</p>` : ""}
              ${task.dependencies?.length ? `<p class="muted small">Depends on: ${task.dependencies.map(esc).join(", ")}</p>` : ""}
            </div>
          </div>
          <div class="task-blockers">
            <span class="field-label">${esc(t("blocking_cases"))}</span>
            <div>${blockerLinks}</div>
          </div>
        </article>`;
    })
    .join("");
  const incomplete = o.incomplete_required_tasks || [];
  return `
    <header class="page-header compact">
      <div>
        <button type="button" class="back" data-nav="#/overview">${esc(t("back_overview"))}</button>
        <h1>${esc(t("close_control_title"))}</h1>
        <p class="muted">${esc(t("close_control_sub"))}</p>
      </div>
      <div class="badge ${o.signoff_ready ? "pass" : "fail"}">
        ${o.signoff_ready ? esc(t("ready_signoff")) : esc(t("signoff_blocked"))}
      </div>
    </header>
    <section class="control-summary">
      <span>${esc(
        t("tasks_complete", {
          done: tasks.filter((tk) => tk.status === "complete").length,
          total: tasks.length,
        })
      )}</span>
      <span>${
        incomplete.length
          ? esc(t("required_gates", { list: incomplete.join(", ") }))
          : esc(t("all_gates"))
      }</span>
    </section>
    <section class="task-list">${rows}</section>
  `;
}

/* ───────── Lines (Accountant) ───────── */

function renderLines() {
  const lines = state.payload.lines || [];
  const ccy = currency();
  const rows = lines
    .map((ln) => {
      const hasCase = !!ln.case_id;
      const action = hasCase
        ? `<button type="button" class="primary" data-nav="#/case/${esc(ln.case_id)}">${
            ln.status === "open" ? esc(t("open_case")) : esc(t("open_case_btn"))
          }</button>`
        : `<span class="muted small">—</span>`;
      return `
        <tr class="${ln.status === "open" ? "line-open" : ""}">
          <td class="mono">${esc(ln.id)}</td>
          <td class="num">${fmt(ln.amount, ln.currency || ccy)}</td>
          <td>
            ${methodBadge(ln.display_method, ln.rule_id)}
            ${partialHint(ln.partial_rule_label)}
            <div class="muted small">${esc(ln.source?.short || ln.source?.file || "")}</div>
          </td>
          <td class="small">${esc(lineStatusText(ln.status))}</td>
          <td class="muted small">${
            ln.mapping?.account
              ? `Proposed account ${esc(ln.mapping.account)}`
              : esc(ln.mapping?.classification || "—")
          }</td>
          <td>${action}</td>
        </tr>`;
    })
    .join("");

  return `
    <header class="page-header compact">
      <div>
        <h1>${esc(t("lines_title"))}</h1>
        <p class="muted">${esc(t("lines_sub"))} · ${lines.length}</p>
      </div>
    </header>
    <div class="lines-wrap">
      <table class="lines-table">
        <thead>
          <tr>
            <th>Line</th>
            <th>Amount</th>
            <th>Source / Provenance</th>
            <th>Status</th>
            <th>Mapping</th>
            <th></th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

/* ───────── Review Queue ───────── */

function filteredCases() {
  const tab = state.queueTab;
  let list = (state.payload.cases || []).filter((c) => {
    if (tab === "resolved") return c.status === "resolved";
    if (tab === "rejected") return c.status === "rejected";
    return c.status === "needs_review";
  });
  if (state.filterReason !== "all") {
    list = list.filter((c) => c.primary_reason === state.filterReason);
  }
  if (state.filterSeverity !== "all") {
    list = list.filter((c) => c.severity === state.filterSeverity);
  }
  if (state.route.query.unassigned === "1") {
    list = list.filter((c) => !c.assigned_to);
  }
  list = [...list].sort((a, b) => {
    const sa = SEVERITY_ORDER[a.severity] ?? 9;
    const sb = SEVERITY_ORDER[b.severity] ?? 9;
    if (sa !== sb) return sa - sb;
    return Math.abs(b.amount || 0) - Math.abs(a.amount || 0);
  });
  return list;
}

function renderQueue() {
  const o = state.payload.overview;
  const list = filteredCases();
  const openCount = (state.payload.cases || []).filter((c) => c.status === "needs_review").length;
  const resolvedCount = (state.payload.cases || []).filter((c) => c.status === "resolved").length;
  const isAdmin = state.role === "fund_admin";
  const title =
    state.role === "fund_manager"
      ? t("queue_title_manager")
      : state.role === "accountant"
        ? t("queue_title_accountant")
        : t("queue_title_admin");

  const rows = list
    .map((c) => {
      const action =
        c.status === "resolved" || c.status === "rejected"
          ? `<button type="button" class="ghost" data-nav="#/history/${esc(c.case_id)}">${esc(
              t("nav_history")
            )}</button>`
          : `<button type="button" class="primary" data-nav="#/case/${esc(c.case_id)}">${esc(
              state.role === "accountant" ? t("prepare") : t("review")
            )}</button>`;
      const assignControl = isAdmin && c.status === "needs_review"
        ? `<label class="assign-inline">${esc(t("owner"))}
            <select data-assign="${esc(c.case_id)}">
              ${ASSIGN_OPTIONS.map(
                (opt) =>
                  `<option value="${esc(opt)}" ${
                    (c.assigned_to || "") === opt ? "selected" : ""
                  }>${opt ? esc(opt) : esc(t("unassigned_opt"))}</option>`
              ).join("")}
            </select>
          </label>`
        : c.assigned_to
          ? `<span class="muted small">${esc(t("owner"))}: ${esc(c.assigned_to)}</span>`
          : `<span class="muted small">${esc(t("unassigned_opt"))}</span>`;
      return `
        <article class="queue-row">
          <div class="queue-main">
            <span class="sev sev-${esc(c.severity)}">${esc((c.severity || "med").toUpperCase())}</span>
            <div>
              <p class="queue-amount">${fmt(c.amount, c.currency)} <span class="muted">${esc(
                c.proposed?.label || ""
              )}</span></p>
              <p class="queue-reason">${esc(c.reason_label)}</p>
              <p class="queue-source muted">${esc(c.source?.short || "")}</p>
              <div class="queue-trust">
                ${methodBadge(c.display_method, c.proposed?.rule_id)}
                ${partialHint(c.partial_rule_label)}
                ${
                  c.candidates?.items?.length
                    ? `<span class="muted small">${esc(
                        t("candidates_drafted", { n: c.candidates.items.length })
                      )}</span>`
                    : ""
                }
                ${
                  c.proposed?.label
                    ? `<span class="proposal-hint muted small">${esc(t("not_a_fact"))}</span>`
                    : ""
                }
              </div>
              ${assignControl}
            </div>
          </div>
          <div class="queue-actions">${action}</div>
        </article>`;
    })
    .join("") || `<p class="empty">${esc(t("no_cases"))}</p>`;

  return `
    <header class="page-header compact">
      <div>
        <button type="button" class="back" data-nav="${
          state.role === "accountant" ? "#/lines" : "#/overview"
        }">${esc(t("back"))}</button>
        <h1>${esc(title)}</h1>
        <p class="muted">${esc(t("shown_open", { shown: list.length, open: openCount }))}</p>
      </div>
    </header>

    <div class="tabs">
      <button type="button" class="tab ${state.queueTab === "open" ? "active" : ""}" data-tab="open">${esc(
        t("tab_open", { n: openCount })
      )}</button>
      <button type="button" class="tab ${state.queueTab === "resolved" ? "active" : ""}" data-tab="resolved">${esc(
        t("tab_resolved", { n: resolvedCount })
      )}</button>
    </div>

    <div class="filters">
      <label>${esc(t("filter_severity"))} ${tip("tip_severity")}
        <select id="filter-severity">
          <option value="all" ${state.filterSeverity === "all" ? "selected" : ""}>${esc(t("all"))}</option>
          <option value="high" ${state.filterSeverity === "high" ? "selected" : ""}>${esc(t("high"))}</option>
          <option value="medium" ${state.filterSeverity === "medium" ? "selected" : ""}>${esc(
            t("medium")
          )}</option>
        </select>
      </label>
      <label>${esc(t("filter_reason"))}
        <select id="filter-reason">
          <option value="all" ${state.filterReason === "all" ? "selected" : ""}>${esc(
            t("all_reasons")
          )}</option>
          ${(o.reason_breakdown || [])
            .map(
              (r) =>
                `<option value="${esc(r.category)}" ${
                  state.filterReason === r.category ? "selected" : ""
                }>${esc(r.label)} (${r.count})</option>`
            )
            .join("")}
        </select>
      </label>
    </div>

    <section class="queue-list">${rows}</section>
  `;
}

/* ───────── Case Detail ───────── */

function productionChain(c) {
  const proposed = c.proposed || {};
  const src = c.source || {};
  const ov = state.payload?.overview || {};
  const steps = [
    {
      key: "source",
      label: t("chain_source"),
      detail: src.file
        ? `${src.file}${src.location ? ` · ${src.location}` : ""}`
        : src.label || "Evidence attached",
      done: !!(src.excerpt || src.file),
    },
    {
      key: "line",
      label: t("chain_line"),
      detail: `${c.line_id || "—"} · ${fmt(c.amount, c.currency)}`,
      done: true,
    },
    {
      key: "mapping",
      label: c.display_method === "Rule" ? t("chain_rule") : t("chain_gap"),
      detail:
        c.display_method === "Rule"
          ? t("chain_rule_applied", { id: proposed.rule_id || "Rule" })
          : c.partial_rule_label ||
            c.reason_label ||
            t("chain_no_rule"),
      done: c.display_method === "Rule" || c.status === "resolved",
    },
    {
      key: "case",
      label: t("chain_case"),
      detail:
        c.status === "needs_review" || c.status === "rejected"
          ? t("chain_open")
          : c.status === "resolved"
            ? t("chain_closed")
            : c.status || "—",
      done: c.status === "resolved",
    },
    {
      key: "decision",
      label: t("chain_decision"),
      detail:
        c.status === "resolved"
          ? `${c.display_method}${
              c.decision?.decided_by ? ` · ${c.decision.decided_by}` : ""
            }`
          : t("chain_not_recorded"),
      done: c.status === "resolved",
    },
    {
      key: "export",
      label: t("chain_export"),
      detail: ov.export_ready
        ? t("chain_export_ready")
        : ov.signed_off
          ? t("chain_export_signed")
          : t("chain_export_after"),
      done: !!ov.export_ready,
    },
  ];
  return `
    <ol class="prod-chain" aria-label="How this line was produced">
      ${steps
        .map(
          (s) => `
        <li class="prod-step ${s.done ? "done" : "pending"}">
          <span class="prod-label">${esc(s.label)}</span>
          <span class="prod-detail">${esc(s.detail)}</span>
        </li>`
        )
        .join("")}
    </ol>`;
}

function renderCaseDetail(c) {
  if (!c) {
    return `<p class="empty">${esc(t("case_not_found"))} <button type="button" data-nav="#/queue">${esc(
      t("back_to_queue")
    )}</button></p>`;
  }
  const whyOpen = !!state.whyOpen[c.case_id];
  const overrideMode = !!state.overrideMode[c.case_id];
  const rejectMode = !!state.rejectMode[c.case_id];
  const proposed = c.proposed || {};
  const src = c.source || {};
  const control = c.control || {};
  const back =
    state.role === "accountant" ? "#/lines" : "#/queue";
  const selected = selectedCandidate(c);
  const acceptTarget = selected
    ? selected.summary
    : proposed.label
      ? `workbook proposal · ${proposed.label}`
      : "workbook proposal";
  const prefill = selected || proposed;
  const decider = canDecideCase();
  const rejecter = canRejectCase();

  let decisionPane;
  if (c.status === "resolved") {
    decisionPane = `
      <div class="col-body">
        <p class="resolved-banner">${esc(c.display_method)} ${esc(t("recorded"))}</p>
        <p>${esc(t("by"))} <strong>${esc(c.decision?.decided_by || "Reviewer")}</strong>${
          c.decision?.role ? ` · ${esc(c.decision.role)}` : ""
        }.</p>
        ${c.decision?.chosen_summary ? `<p class="small">${esc(t("chosen"))}: ${esc(c.decision.chosen_summary)}</p>` : ""}
        ${c.decision?.final_summary ? `<p class="small">${esc(t("final"))}: ${esc(c.decision.final_summary)}</p>` : ""}
        ${c.decision?.reason ? `<p class="history-row-reason">${esc(c.decision.reason)}</p>` : ""}
        ${c.decision?.timestamp ? `<p class="muted small">${esc(fmtDate(c.decision.timestamp))}</p>` : ""}
        <button type="button" class="primary" data-nav="#/history/${esc(c.case_id)}">${esc(
          t("view_case_history")
        )}</button>
      </div>`;
  } else if (!decider) {
    decisionPane = `
      <div class="col-body">
        <p class="resolved-banner">${esc(t("prepare_only"))}</p>
        <p class="small">${esc(t("prepare_only_body"))}</p>
        <p class="muted small">${esc(t("switch_to_decide"))}</p>
        ${renderCandidates(c)}
      </div>`;
  } else {
    decisionPane = `
      <div class="col-body">
        <p class="muted small decision-hint">${esc(t("tip_decision"))}</p>
        ${
          c.status === "rejected"
            ? `<p class="resolved-banner">${esc(t("rejected_banner"))}</p>
               ${c.decision?.reason ? `<p class="history-row-reason">${esc(c.decision.reason)}</p>` : ""}`
            : ""
        }
        <button type="button" class="primary block" data-accept="${esc(c.case_id)}">${acceptLabel()}</button>
        <p class="muted small accept-target">${
          state.role === "fund_manager" ? esc(t("approves")) : esc(t("accepts"))
        }: ${esc(acceptTarget)}</p>
        ${
          overrideMode
            ? `
          <div class="override-box">
            <label>${esc(t("override_reason"))} <span class="req">${esc(
                t("reason_required", { n: MIN_REASON_LEN })
              )}</span>
              <textarea id="override-reason" placeholder="${esc(t("override_placeholder"))}"></textarea>
            </label>
            ${reasonCounterHtml("override-reason")}
            <label>${esc(t("final_classification"))}
              <input id="override-class" type="text" value="${esc(prefill.classification || prefill.label || "")}" />
            </label>
            <label>${esc(t("final_account"))}
              <input id="override-account" type="text" value="${esc(prefill.account || "")}" />
            </label>
            <label>${esc(t("final_project"))}
              <input id="override-project" type="text" value="${esc(prefill.project_code || "")}" />
            </label>
            <div class="row-actions">
              <button type="button" class="primary" data-override-commit="${esc(c.case_id)}">${esc(
                t("commit_override")
              )}</button>
              <button type="button" data-override-cancel="${esc(c.case_id)}">${esc(t("cancel"))}</button>
            </div>
          </div>`
            : `<button type="button" class="block" data-override-open="${esc(c.case_id)}">${esc(
                t("override")
              )}</button>`
        }
        ${
          rejecter
            ? rejectMode
              ? `
          <div class="override-box">
            <label>${esc(t("reject_reason"))} <span class="req">${esc(
                  t("reason_required", { n: MIN_REASON_LEN })
                )}</span>
              <textarea id="reject-reason" placeholder="${esc(t("reject_placeholder"))}"></textarea>
            </label>
            ${reasonCounterHtml("reject-reason")}
            <div class="row-actions">
              <button type="button" class="danger" data-reject-commit="${esc(c.case_id)}">${esc(
                t("confirm_reject")
              )}</button>
              <button type="button" data-reject-cancel="${esc(c.case_id)}">${esc(t("cancel"))}</button>
            </div>
          </div>`
              : `<button type="button" class="block ghost" data-reject-open="${esc(c.case_id)}">${esc(
                  t("reject")
                )}</button>`
            : `<p class="muted small">${esc(t("reject_admin_only"))}</p>`
        }
      </div>`;
  }

  return `
    <header class="page-header compact">
      <div>
        <button type="button" class="back" data-nav="${back}">${esc(t("back"))}</button>
        <h1>${esc(c.case_id)}</h1>
        <p class="muted">${fmt(c.amount, c.currency)} · ${esc(c.reason_label || "")}</p>
        ${c.assigned_to ? `<p class="muted small">${esc(t("owner"))}: ${esc(c.assigned_to)}</p>` : ""}
      </div>
      <div class="header-badges">
        ${methodBadge(c.display_method, proposed.rule_id)}
        <span class="sev sev-${esc(c.severity)}">${esc((c.severity || "").toUpperCase())}</span>
      </div>
    </header>

    <section class="detail-grid">
      <div class="detail-col">
        <h2>${esc(t("source"))} ${tip("tip_source")}</h2>
        <div class="col-body">
          <p class="field-label">${esc(t("document"))}</p>
          <p>${esc(src.label)}</p>
          <p class="field-label">${esc(t("location"))}</p>
          <p>${esc(src.location)}${src.file ? ` · <span class="mono">${esc(src.file)}</span>` : ""}</p>
          <p class="field-label">${esc(t("amount"))}</p>
          <p class="amount">${fmt(c.amount, c.currency)}</p>
          <p class="field-label">${esc(t("description"))}</p>
          <p>${esc(c.description)}</p>
          <button type="button" class="ghost" data-view-source="${esc(c.case_id)}">${esc(
            t("view_source")
          )}</button>
          <pre class="excerpt hidden" id="source-excerpt">${esc(src.excerpt)}</pre>
        </div>
      </div>

      <div class="detail-col">
        <h2>${esc(t("how_produced"))} ${tip("tip_how_produced")}</h2>
        <div class="col-body">
          ${productionChain(c)}
          <p class="field-label">${esc(t("provenance"))}</p>
          <p>${methodBadge(c.display_method, proposed.rule_id)}</p>
          ${c.partial_rule_label ? `<p class="small">${esc(c.partial_rule_label)}</p>` : ""}
          ${proposed.rule ? `<p class="muted small">${esc(proposed.rule)}</p>` : ""}
          <p class="field-label">${esc(t("workbook_proposal"))} <span class="muted">${esc(
            t("not_a_fact")
          )}</span> ${tip("tip_workbook_proposal")}</p>
          <p>${esc(proposed.label || t("none"))}</p>
          ${proposed.account ? `<p class="muted small">Account ${esc(proposed.account)}</p>` : ""}
          ${proposed.project_code ? `<p class="muted small">Project ${esc(proposed.project_code)}</p>` : ""}
          <p class="field-label">${esc(t("source_match"))}</p>
          <p class="small">${esc(proposed.match)}</p>
          <button type="button" class="ghost" data-toggle-why="${esc(c.case_id)}">
            ${whyOpen ? esc(t("hide_why")) : esc(t("why_case"))}
          </button>
          ${
            whyOpen
              ? `<div class="why-box"><p>${esc(c.why_sentence)}</p>
                 <p class="muted small">${esc(t("source"))}: ${esc(src.short)}</p></div>`
              : ""
          }
          ${decider ? renderCandidates(c) : ""}
        </div>
      </div>

      <div class="detail-col control-col">
        <h2>${esc(t("control"))}</h2>
        <div class="col-body">
          <p class="field-label">${esc(t("recon_category"))}</p>
          <p>${esc(String(control.recon_category || "unidentified").replace(/_/g, " "))}</p>
          <p class="field-label">${esc(t("materiality"))}</p>
          <p><span class="sev sev-${esc(control.materiality_tier || c.severity || "medium")}">${esc((control.materiality_tier || c.severity || "medium").toUpperCase())}</span></p>
          <p class="field-label">${esc(t("control_ownership"))}</p>
          <p class="small">${esc(t("preparer"))}: ${esc(control.preparer || "Fund Accountant")}<br />${esc(
            t("reviewer")
          )}: ${esc(control.reviewer || "Fund Admin")}</p>
          <p class="field-label">${esc(t("clearance_target"))}</p>
          <p class="small">${esc(control.clearance_target || "Resolve or escalate before batch sign-off")}</p>
          ${control.due_at ? `<p class="muted small">Due ${esc(fmtDate(control.due_at))}</p>` : ""}
        </div>
      </div>

      <div class="detail-col decision-col">
        <h2>${esc(t("decision"))} ${tip("tip_decision")}</h2>
        ${decisionPane}
      </div>
    </section>
  `;
}

/* ───────── Candidates (drafts, never a Method) ───────── */

function selectedCandidate(c) {
  const items = c.candidates?.items || [];
  const idx = state.selectedCandidate[c.case_id];
  if (idx === undefined || idx === null) return null;
  return items.find((it) => it.index === idx) || null;
}

function evidenceChips(evidence) {
  return (evidence || [])
    .map((e) => `<span class="evidence-chip">${esc(e.type)} · ${esc(e.ref)}</span>`)
    .join("");
}

function renderCandidates(c) {
  const open = c.status === "needs_review" || c.status === "rejected";
  const cand = c.candidates;
  const llm = state.payload?.llm;
  const sel = state.selectedCandidate[c.case_id];

  let list = "";
  if (cand?.items?.length) {
    const modelBit = cand.model ? ` · ${cand.model}` : "";
    list = `
      <ul class="candidate-list">
        ${cand.items
          .map(
            (it) => `
          <li class="candidate ${sel === it.index ? "selected" : ""}">
            <label>
              ${
                open
                  ? `<input type="radio" name="candidate-${esc(c.case_id)}" data-candidate="${it.index}" ${
                      sel === it.index ? "checked" : ""
                    } />`
                  : ""
              }
              <span class="candidate-body">
                <strong>${esc(it.treatment || "Candidate")}</strong>
                <span class="small">${[
                  it.classification ? `classification ${esc(it.classification)}` : "",
                  it.account ? `account ${esc(it.account)}` : "",
                  it.project_code ? `project ${esc(it.project_code)}` : "",
                ]
                  .filter(Boolean)
                  .join(" · ")}</span>
                ${it.rationale ? `<span class="candidate-rationale">${esc(it.rationale)}</span>` : ""}
                <span class="evidence">${evidenceChips(it.evidence)}</span>
              </span>
            </label>
          </li>`
          )
          .join("")}
      </ul>
      ${cand.note ? `<p class="muted small">${esc(cand.note)}</p>` : ""}
      <p class="muted small">${esc(
        t("candidates_footer", {
          at: cand.drafted_at || "",
          model: modelBit,
        })
      )}</p>`;
  }

  let action = "";
  if (open && llm?.enabled) {
    action = `<button type="button" class="block" data-draft-candidates="${esc(c.case_id)}">${esc(
      cand?.items?.length ? t("redraft_candidates") : t("draft_candidates")
    )}</button>
    <p class="muted small">${esc(t("draft_hint"))}</p>`;
  } else if (open && llm && !llm.enabled && !cand?.items?.length) {
    action = `<p class="muted small">${esc(t("draft_off"))}</p>`;
  }

  if (!list && !action) return "";
  return `
    <p class="field-label">${esc(t("candidates"))} ${tip("tip_candidates")}</p>
    ${list}
    ${action}`;
}

/* ───────── Decision History ───────── */

function actionLabel(action) {
  if (action === "sign_off") return t("action_sign_off");
  if (action === "accept") return t("action_accept");
  if (action === "override") return t("action_override");
  if (action === "reject") return t("action_reject");
  return action || t("action_accept");
}

function renderBatchHistory() {
  const list = [...(state.payload.decisions || [])].sort((a, b) =>
    String(b.timestamp || "").localeCompare(String(a.timestamp || ""))
  );
  const ccy = currency();
  const rows =
    list
      .map((d) => {
        const isBatch = d.scope === "batch" || d.action === "sign_off";
        const jump = isBatch
          ? ""
          : `<button type="button" class="ghost" data-nav="#/case/${esc(
              d.case_id
            )}">${esc(t("open_case_btn"))}</button>
             <button type="button" class="ghost" data-nav="#/history/${esc(
               d.case_id
             )}">${esc(t("case_timeline_btn"))}</button>`;
        return `
        <article class="history-row ${isBatch ? "batch" : ""}">
          <div class="history-row-main">
            <div class="history-row-meta">
              <span class="pill ${isBatch ? "decision" : "rule"}">${esc(
                actionLabel(d.action)
              )}</span>
              ${
                d.case_id
                  ? `<span class="muted mono">${esc(d.case_id)}</span>`
                  : `<span class="muted">Batch</span>`
              }
              ${d.role ? `<span class="muted small">${esc(d.role)}</span>` : ""}
              ${d.timestamp ? `<span class="muted small">${esc(d.timestamp)}</span>` : ""}
            </div>
            <p class="history-row-title">
              ${esc(d.decided_by || "Reviewer")}
              ${
                d.amount != null
                  ? `<span class="muted"> · ${fmt(d.amount, d.currency || ccy)}</span>`
                  : ""
              }
            </p>
            ${d.reason_label ? `<p class="muted small">${esc(d.reason_label)}</p>` : ""}
            ${d.reason ? `<p class="history-row-reason">${esc(d.reason)}</p>` : ""}
            ${
              d.candidate_count
                ? `<p class="muted small">${d.candidate_count} candidate(s) shown${
                    d.chosen_summary ? ` · chosen: ${esc(d.chosen_summary)}` : " · none chosen"
                  }</p>`
                : ""
            }
            ${
              d.final_summary
                ? `<p class="muted small">Final: ${esc(d.final_summary)}</p>`
                : ""
            }
          </div>
          <div class="history-row-actions">${jump}</div>
        </article>`;
      })
      .join("") || `<p class="empty">No decisions recorded yet.</p>`;

  return `
    <header class="page-header compact">
      <div>
        <h1>${esc(t("history_title"))}</h1>
        <p class="muted">${esc(t("history_sub"))} · ${list.length}</p>
      </div>
    </header>
    <div class="history-list">${rows}</div>
  `;
}

function renderCaseHistory(c) {
  if (!c) {
    return `<p class="empty">Case not found. <button type="button" data-nav="#/history">Back to history</button></p>`;
  }
  const items = (c.history || [])
    .map((h) => {
      let body = h.detail ? `<p>${esc(h.detail)}</p>` : "";
      if (h.candidates && h.candidates.length) {
        body += `<ul class="timeline-candidates">${h.candidates
          .map(
            (s) =>
              `<li class="${h.chosen && s === h.chosen ? "chosen" : ""}">${esc(s)}${
                h.chosen && s === h.chosen ? " <span class=\"chosen-tag\">chosen</span>" : ""
              }</li>`
          )
          .join("")}</ul>`;
      }
      if (h.previous || h.final) {
        body += `<p class="history-diff">
          ${h.previous ? `<span>Previous: ${esc(h.previous)}</span>` : ""}
          ${h.final ? `<span>Final: ${esc(h.final)}</span>` : ""}
        </p>`;
      }
      if (h.rule) body += `<p class="muted small">${esc(h.rule)}</p>`;
      return `
        <li class="timeline-item">
          <div class="timeline-meta">
            <span class="timeline-actor">${esc(h.actor)}${h.role ? ` · ${esc(h.role)}` : ""}</span>
            ${h.at ? `<span class="muted small">${esc(h.at)}</span>` : ""}
          </div>
          <strong>${esc(h.event)}</strong>
          ${body}
        </li>`;
    })
    .join("");

  return `
    <header class="page-header compact">
      <div>
        <button type="button" class="back" data-nav="#/history">${esc(t("all_decisions"))}</button>
        <h1>${esc(t("case_timeline"))}</h1>
        <p class="muted">${esc(c.case_id)} · ${fmt(c.amount, c.currency)}</p>
      </div>
    </header>
    <ol class="timeline">${items}</ol>
    <p class="row-actions">
      <button type="button" data-nav="#/case/${esc(c.case_id)}">${esc(t("open_case_btn"))}</button>
      <button type="button" data-nav="#/queue?tab=resolved">${esc(t("resolved_queue"))}</button>
    </p>
  `;
}

/* ───────── Shell / routing ───────── */

function render() {
  const app = document.getElementById("app");
  if (!state.payload) {
    app.innerHTML = `<p class="loading">${esc(t("loading"))}</p>`;
    return;
  }
  state.route = parseHash();
  const q = state.route.query;
  if (state.route.name === "queue") {
    state.filterReason = q.reason || state.filterReason || "all";
    if (q.severity) state.filterSeverity = q.severity;
    else if (state.role === "fund_manager" && state.filterSeverity === "all") {
      state.filterSeverity = "high";
    }
    if (q.tab === "resolved") state.queueTab = "resolved";
    else if (!q.tab) state.queueTab = state.queueTab || "open";
  }

  let body = "";
  if (state.route.name === "lines") body = renderLines();
  else if (state.route.name === "control") body = renderCloseControl();
  else if (state.route.name === "queue") body = renderQueue();
  else if (state.route.name === "case") body = renderCaseDetail(findCase(state.route.params.id));
  else if (state.route.name === "case-history")
    body = renderCaseHistory(findCase(state.route.params.id));
  else if (state.route.name === "history") body = renderBatchHistory();
  else body = renderOverview();

  const flash = state.flash
    ? `<div class="flash">${esc(state.flash)}</div>`
    : "";

  const drafts = state.payload?.llm?.enabled
    ? ` · ${esc(t("footer_drafts_on", { model: state.payload.llm.model }))}`
    : ` · ${esc(t("footer_drafts_off"))}`;

  app.innerHTML = `${flash}${renderTopNav()}<div class="shell">${body}</div>
    <footer>${esc(t("footer"))} ${esc(t("footer_role"))}: ${esc(state.role)}${drafts}</footer>
    ${renderGuideModal()}`;
  bind();
}

function bind() {
  document.querySelectorAll("[data-nav]").forEach((el) => {
    el.addEventListener("click", () => navigate(el.getAttribute("data-nav")));
  });

  const roleSelect = document.getElementById("role-select");
  if (roleSelect) {
    roleSelect.addEventListener("change", () => setRole(roleSelect.value));
  }

  document.querySelectorAll("[data-lang]").forEach((el) => {
    el.addEventListener("click", () => setLang(el.getAttribute("data-lang")));
  });

  document.querySelectorAll(".tip-btn").forEach((el) => {
    el.addEventListener("click", (ev) => {
      ev.preventDefault();
      ev.stopPropagation();
    });
  });

  document.querySelectorAll("[data-open-guide]").forEach((el) => {
    el.addEventListener("click", () => {
      state.guideOpen = true;
      render();
    });
  });

  document.querySelectorAll("[data-close-guide]").forEach((el) => {
    el.addEventListener("click", (ev) => {
      // Overlay click (target is overlay) or explicit close button.
      if (el.classList.contains("guide-overlay") && ev.target !== el) return;
      state.guideOpen = false;
      render();
    });
  });

  const guidePanel = document.querySelector("[data-guide-panel]");
  if (guidePanel) {
    guidePanel.addEventListener("click", (ev) => ev.stopPropagation());
  }

  document.querySelectorAll("[data-tab]").forEach((el) => {
    el.addEventListener("click", () => {
      state.queueTab = el.getAttribute("data-tab");
      if (state.queueTab === "resolved") {
        navigate("#/queue?tab=resolved");
      } else {
        navigate(queueHash());
      }
      render();
    });
  });

  const sev = document.getElementById("filter-severity");
  if (sev) {
    sev.addEventListener("change", () => {
      state.filterSeverity = sev.value;
      navigate(queueHash());
      render();
    });
  }
  const reasonSel = document.getElementById("filter-reason");
  if (reasonSel) {
    reasonSel.addEventListener("change", () => {
      state.filterReason = reasonSel.value;
      navigate(queueHash());
      render();
    });
  }

  document.querySelectorAll("[data-candidate]").forEach((el) => {
    el.addEventListener("change", () => {
      const caseId = state.route.params.id;
      state.selectedCandidate[caseId] = Number(el.getAttribute("data-candidate"));
      render();
    });
  });

  document.querySelectorAll("[data-assign]").forEach((el) => {
    el.addEventListener("change", () => {
      postAssign(el.getAttribute("data-assign"), el.value);
    });
  });

  document.querySelectorAll("[data-toggle-why]").forEach((el) => {
    el.addEventListener("click", () => {
      const id = el.getAttribute("data-toggle-why");
      state.whyOpen[id] = !state.whyOpen[id];
      render();
    });
  });

  document.querySelectorAll("[data-view-source]").forEach((el) => {
    el.addEventListener("click", () => {
      const pre = document.getElementById("source-excerpt");
      if (pre) pre.classList.toggle("hidden");
    });
  });

  document.querySelectorAll("[data-override-open]").forEach((el) => {
    el.addEventListener("click", () => {
      const id = el.getAttribute("data-override-open");
      state.overrideMode[id] = true;
      state.rejectMode[id] = false;
      render();
    });
  });
  document.querySelectorAll("[data-override-cancel]").forEach((el) => {
    el.addEventListener("click", () => {
      state.overrideMode[el.getAttribute("data-override-cancel")] = false;
      render();
    });
  });

  document.querySelectorAll("[data-reject-open]").forEach((el) => {
    el.addEventListener("click", () => {
      const id = el.getAttribute("data-reject-open");
      state.rejectMode[id] = true;
      state.overrideMode[id] = false;
      render();
    });
  });
  document.querySelectorAll("[data-reject-cancel]").forEach((el) => {
    el.addEventListener("click", () => {
      state.rejectMode[el.getAttribute("data-reject-cancel")] = false;
      render();
    });
  });

  document.querySelectorAll("[data-accept]").forEach((el) => {
    el.addEventListener("click", () => postDecision(el.getAttribute("data-accept"), "accept"));
  });
  document.querySelectorAll("[data-override-commit]").forEach((el) => {
    el.addEventListener("click", () =>
      postDecision(el.getAttribute("data-override-commit"), "override")
    );
  });
  document.querySelectorAll("[data-reject-commit]").forEach((el) => {
    el.addEventListener("click", () => postDecision(el.getAttribute("data-reject-commit"), "reject"));
  });

  document.querySelectorAll("[data-draft-candidates]").forEach((el) => {
    el.addEventListener("click", () =>
      draftCandidates(el.getAttribute("data-draft-candidates"), el)
    );
  });

  const signOffBtn = document.querySelector("[data-sign-off]");
  if (signOffBtn) {
    signOffBtn.addEventListener("click", () => postSignOff());
  }
  const exportBtn = document.querySelector("[data-export]");
  if (exportBtn) {
    exportBtn.addEventListener("click", () => downloadExport());
  }

  document.querySelectorAll("#override-reason, #reject-reason").forEach((el) => {
    el.addEventListener("input", updateReasonCounters);
  });
  updateReasonCounters();
}

async function postAssign(caseId, assignedTo) {
  try {
    const res = await fetch("/api/assign", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        case_id: caseId,
        assigned_to: assignedTo || null,
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      alert(data.error || "Assign failed");
      return;
    }
    state.flash = assignedTo
      ? `Assigned ${caseId} → ${assignedTo}`
      : `Cleared owner on ${caseId}`;
    await load(false);
  } catch (err) {
    console.error(err);
    alert("Could not assign case");
  }
}

function queueHash() {
  const bits = [];
  if (state.filterReason !== "all") bits.push(`reason=${state.filterReason}`);
  if (state.filterSeverity !== "all") bits.push(`severity=${state.filterSeverity}`);
  return `#/queue${bits.length ? `?${bits.join("&")}` : ""}`;
}

async function draftCandidates(caseId, btn) {
  const original = btn ? btn.textContent : "";
  if (btn) {
    btn.disabled = true;
    btn.textContent = "Drafting…";
  }
  try {
    const res = await fetch("/api/suggest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ case_id: caseId }),
    });
    const data = await res.json();
    if (!res.ok) {
      alert(data.error || "Could not draft candidates");
      return;
    }
    const n = data.candidates?.candidates?.length || 0;
    delete state.selectedCandidate[caseId];
    state.flash = `${n} candidate(s) drafted on ${caseId} · still Unresolved until you Accept or Override`;
    await load(false);
    navigate(`#/case/${caseId}`, { keepFlash: true });
  } catch (err) {
    console.error(err);
    alert("Could not reach the candidate service");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = original;
    }
  }
}

async function postDecision(caseId, action) {
  const c = findCase(caseId);
  if (!c) return;

  if (action === "reject" && !canRejectCase()) {
    alert("Reject is Fund Admin only.");
    return;
  }
  if ((action === "accept" || action === "override") && !canDecideCase()) {
    alert("Accountant prepares Cases. Switch to Fund Admin to Decide, or Fund Manager to Approve.");
    return;
  }

  let reason;
  let finalValue = {};
  let chosenIndex = null;
  const proposed = c.proposed || {};
  const selected = selectedCandidate(c);

  if (action === "accept") {
    const verb = state.role === "fund_manager" ? "Approved" : "Accepted";
    if (selected) {
      chosenIndex = selected.index;
      reason = `${verb} candidate: ${selected.treatment}`;
      if (selected.account) finalValue.account = selected.account;
      if (selected.classification) finalValue.classification = selected.classification;
      if (selected.project_code) finalValue.project_code = selected.project_code;
    } else {
      reason = `${verb} workbook proposal`;
      if (proposed.account) finalValue.account = proposed.account;
      if (proposed.classification) finalValue.classification = proposed.classification;
      if (proposed.project_code) finalValue.project_code = proposed.project_code;
    }
    if (!Object.keys(finalValue).length) {
      alert("Nothing to accept: pick a candidate or use Override to enter a treatment.");
      return;
    }
  } else if (action === "reject") {
    const reasonEl = document.getElementById("reject-reason");
    reason = (reasonEl?.value || "").trim();
    if (reason.length < MIN_REASON_LEN) {
      alert(`Reject needs a reason of at least ${MIN_REASON_LEN} characters.`);
      return;
    }
    finalValue = {};
  } else {
    const reasonEl = document.getElementById("override-reason");
    reason = (reasonEl?.value || "").trim();
    if (reason.length < MIN_REASON_LEN) {
      alert(`Override needs a reason of at least ${MIN_REASON_LEN} characters.`);
      return;
    }
    const cls = (document.getElementById("override-class")?.value || "").trim();
    const acct = (document.getElementById("override-account")?.value || "").trim();
    const proj = (document.getElementById("override-project")?.value || "").trim();
    if (cls) finalValue.classification = cls;
    if (acct) finalValue.account = acct;
    if (proj) finalValue.project_code = proj;
    if (!Object.keys(finalValue).length) {
      alert("Provide at least a final classification or account.");
      return;
    }
  }

  try {
    // Candidates are snapshotted server-side from the Case record; the
    // browser only reports which one (if any) was accepted.
    const res = await fetch("/api/decision", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        case_id: caseId,
        action,
        decided_by: REVIEWER,
        role: state.role,
        reason,
        final_value: finalValue,
        chosen_candidate_index: chosenIndex,
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      alert(data.error || "Decision failed");
      return;
    }
    if (action === "accept") {
      state.flash = `Decision recorded on ${caseId} · ${REVIEWER} (${state.role})`;
    } else if (action === "reject") {
      state.flash = `Reject recorded on ${caseId} — stays Unresolved`;
    } else {
      state.flash = `Override recorded on ${caseId} · ${REVIEWER} (${state.role})`;
    }
    state.overrideMode[caseId] = false;
    state.rejectMode[caseId] = false;
    delete state.selectedCandidate[caseId];
    await load(false);
    navigate(`#/history/${caseId}`, { keepFlash: true });
  } catch (err) {
    console.error(err);
    alert("Could not record decision");
  }
}

async function postSignOff() {
  if (!canSignOff()) {
    alert("Sign-off requires zero open cases and a PASS tie-out.");
    return;
  }
  try {
    const res = await fetch("/api/decision", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: "sign_off",
        decided_by: REVIEWER,
        role: state.role,
        reason: "Batch signed off — all open cases resolved; tie-out PASS.",
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      alert(data.error || "Sign-off failed");
      return;
    }
    state.flash = `Batch signed off · download validated export from Overview`;
    await load(false);
    navigate("#/overview", { keepFlash: true });
  } catch (err) {
    console.error(err);
    alert("Could not record sign-off");
  }
}

async function downloadExport() {
  if (!canExport()) {
    const blockers = state.payload?.overview?.export_blockers || [];
    alert(
      blockers.length
        ? "Export blocked:\n- " + blockers.join("\n- ")
        : "Export is not ready"
    );
    return;
  }
  const profile =
    state.payload?.overview?.export_profile || "validated_mapping_csv_v1";
  try {
    const res = await fetch(
      `/api/export?profile=${encodeURIComponent(profile)}`
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const detail =
        (err.blockers && err.blockers.join("; ")) || err.error || res.statusText;
      throw new Error(detail);
    }
    const blob = await res.blob();
    const disposition = res.headers.get("Content-Disposition") || "";
    const match = /filename="([^"]+)"/.exec(disposition);
    const fileName = match ? match[1] : "validated_mapping.csv";
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    state.flash = `Downloaded ${fileName}`;
    render();
  } catch (err) {
    console.error(err);
    alert("Could not download export: " + (err.message || err));
  }
}

async function load(showLoading = true) {
  if (showLoading) {
    document.getElementById("app").innerHTML = `<p class="loading">${esc(t("loading"))}</p>`;
  }
  const res = await fetch("/api/close");
  if (!res.ok) throw new Error("Failed to load /api/close");
  state.payload = await res.json();
  render();
}

window.addEventListener("hashchange", () => {
  render();
});

window.addEventListener("keydown", (ev) => {
  if (ev.key === "Escape" && state.guideOpen) {
    state.guideOpen = false;
    render();
  }
});

load().catch((err) => {
  document.getElementById("app").innerHTML =
    `<p class="empty">${esc(t("load_error"))}</p>`;
  console.error(err);
});
