import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = process.cwd();
const zh14Path = path.join(root, "docs", "zh", "14_bps_driven_servicer_fcl_interface.md");
const zh13Path = path.join(root, "docs", "zh", "13_newrez_fcl_bps_display_mapping.md");
const outputDir = path.join(root, "outputs", "doc14_servicer_fcl_interface_review");
const outputPath = path.join(outputDir, "Doc14_Servicer_FCL_Interface_Business_Review.xlsx");

const today = "2026-05-31";

function stripMd(value) {
  return String(value ?? "")
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/\*([^*]+)\*/g, "$1")
    .replace(/✅/g, "Provided")
    .replace(/⚠️|⚠/g, "Partial")
    .replace(/❌/g, "Missing")
    .replace(/🟡/g, "Partial")
    .replace(/🔮/g, "Reserved")
    .replace(/—/g, "-")
    .trim();
}

function splitTableLine(line) {
  const trimmed = line.trim();
  const inner = trimmed.startsWith("|") ? trimmed.slice(1, trimmed.endsWith("|") ? -1 : undefined) : trimmed;
  return inner.split("|").map((cell) => stripMd(cell));
}

function isSep(line) {
  return /^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$/.test(line);
}

function sectionBucket(heading) {
  const h = heading || "";
  if (/2\.0|四维状态/.test(h)) return "00 四维状态基础";
  if (/2\.1|贷款识别/.test(h)) return "01 贷款识别与入库";
  if (/2\.2|FCL 状态/.test(h)) return "02 FCL Summary 状态";
  if (/2\.3|Timeline|时间线/.test(h)) return "03 FCL Timeline";
  if (/2\.4|Hold/.test(h)) return "04 Hold 暂停";
  if (/2\.5|竞拍|Bid/.test(h)) return "05 Bid / Sale";
  if (/2\.6|风险增强|贷款属性/.test(h)) return "06 贷款属性与风险增强";
  if (/3\.1|Loss Mitigation|损失缓解|LM/.test(h)) return "07 Loss Mitigation";
  if (/4\.1|Bankruptcy|破产/.test(h)) return "08 Bankruptcy";
  if (/5\.1|合规矩阵/.test(h)) return "09 合规矩阵";
  if (/附录 A/.test(h)) return "10 面板字段矩阵";
  if (/附录 B/.test(h)) return "11 ETL中间表";
  return "99 其他";
}

function primaryPanel(text, heading) {
  const t = `${text || ""} ${heading || ""}`;
  if (/Loss Mitigation|LM Cycle|LM/.test(t)) return "Loss Mitigation Cycle";
  if (/Bankruptcy|BK|破产/.test(t)) return "Bankruptcy";
  if (/Hold|暂停/.test(t)) return "Hold";
  if (/Aggregate Stage|Stage Tab|阶段/.test(t)) return "Aggregate Stage Tab";
  if (/Aggregate Time Line|Time Line Tab/.test(t)) return "Aggregate Time Line Tab";
  if (/Timeline|Milestone|时间线|timeline_|NOI|Referral|First Legal|Service|Publication|Judgement|Sale/.test(t)) return "FCL Milestone Timeline";
  if (/Summary|summary_|摘要|Current Step|Attorney|Days in FCL/.test(t)) return "FCL Summary";
  if (/Bid|竞拍|Sale Amount|拍卖/.test(t)) return "Bid Approval / Sale";
  return "Cross-panel / Foundation";
}

function priorityOf(row) {
  const text = Object.values(row).join(" ");
  if (/\bP0\b/.test(text)) return "P0";
  if (/\bP1\b/.test(text)) return "P1";
  if (/\bP2\b/.test(text)) return "P2";
  return "";
}

function normalizePriority(value) {
  const text = String(value || "");
  if (/\bP0\b/.test(text)) return "P0";
  if (/\bP1\b/.test(text)) return "P1";
  if (/\bP2\b/.test(text)) return "P2";
  return "";
}

function statusCategory(status) {
  const s = status || "";
  if (/Missing|未提供|0%|无对应|不存在|恒NULL/.test(s)) return "Missing";
  if (/Partial|部分|偏低|低|~0%|填充率/.test(s)) return "Partial";
  if (/Derived|推导|N\/A/.test(s)) return "Derived";
  if (/Provided|已提供|100%|✅/.test(s)) return "Provided";
  return "Review";
}

function defaultSourceTable(section, field, rawField) {
  const text = `${section} ${field} ${rawField}`;
  if (/portnewrezpmt|nextduedate/.test(text)) return "newrez.portnewrezpmt";
  if (/portnewrezgeneral|mbadelinquency|investor|lien|interest_paid|reason_for_default/i.test(text)) return "newrez.portnewrezgeneral";
  if (/Loss Mitigation|损失缓解|LM|dealstartdate|lmremovaldate|lmdeal|lmprogram|lmstatus|lmdecision|borrowerintention/i.test(text)) return "newrez.portnewrezlm";
  if (/Bankruptcy|破产|BK|bk|mfr|poc|debtor/i.test(text)) return "newrez.portnewrezbk";
  return "newrez.portnewrezfc";
}

function fullDbFieldPath(section, field, rawField) {
  const raw = stripMd(rawField);
  if (!raw || /\(无|无对应|none|未提供|no field|N\/A|ETL 推导|推导|\*/i.test(raw)) return raw || "N/A";
  const base = defaultSourceTable(section, field, raw);
  const matches = [];
  const explicit = raw.match(/[a-zA-Z_][\w]*\.[a-zA-Z_][\w]*\.[a-zA-Z_][\w]*/g);
  if (explicit) matches.push(...explicit);
  const tokens = raw.match(/[a-zA-Z_][\w]*/g) || [];
  for (const token of tokens) {
    if ([
      "from", "source", "table", "DATE", "VARCHAR", "TINYINT", "INTEGER", "Newrez", "BPS",
      "YYYY", "MM", "DD", "ETL", "COALESCE", "NULL", "IS", "NOT", "AND", "OR", "TRUE", "FALSE",
      "来源表", "DATE"
    ].includes(token)) continue;
    if (/^(portnewrezfc|portnewrezpmt|portnewrezlm|portnewrezbk|portnewrezgeneral|newrez)$/i.test(token)) continue;
    if (/^\d/.test(token)) continue;
    if (!matches.includes(`${base}.${token}`)) matches.push(`${base}.${token}`);
  }
  return matches.length ? matches.join("; ") : raw;
}

function readTables(markdown) {
  const lines = markdown.split(/\r?\n/);
  const tables = [];
  let heading = "";
  let expectingMeaning = false;
  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i];
    const headingMatch = /^(#{2,4})\s+(.+)$/.exec(line);
    if (headingMatch) {
      heading = stripMd(headingMatch[2]);
      expectingMeaning = false;
    }
    if (/业务含义\/计算逻辑/.test(line)) expectingMeaning = true;
    if (!line.trim().startsWith("|")) continue;
    const block = [];
    while (i < lines.length && lines[i].trim().startsWith("|")) {
      block.push(lines[i]);
      i += 1;
    }
    i -= 1;
    if (block.length < 2 || !isSep(block[1])) continue;
    const headers = splitTableLine(block[0]);
    const rows = block.slice(2).filter((r) => !isSep(r)).map((r) => {
      const cells = splitTableLine(r);
      const out = {};
      headers.forEach((h, idx) => {
        out[h || `col_${idx + 1}`] = cells[idx] ?? "";
      });
      return out;
    });
    tables.push({ heading, headers, rows, isMeaning: expectingMeaning && headers.length === 2 });
    expectingMeaning = false;
  }
  return tables;
}

function getFieldValue(row, names) {
  for (const name of names) {
    if (row[name] !== undefined) return row[name];
  }
  return "";
}

function buildFieldRows(tables) {
  const specRows = [];
  const meaningByField = new Map();

  for (const table of tables) {
    const hasStandardField = table.headers.some((h) => /标准接口字段名|Standard Interface Field/.test(h));
    if (!hasStandardField) continue;
    if (table.isMeaning || table.headers.some((h) => /业务含义\/计算逻辑/.test(h))) {
      for (const row of table.rows) {
        const field = getFieldValue(row, ["标准接口字段名", "Standard Interface Field"]);
        const meaning = getFieldValue(row, ["业务含义/计算逻辑", "Business Meaning / Calculation Logic"]);
        if (field) meaningByField.set(field, meaning);
      }
      continue;
    }
    for (const row of table.rows) {
      const field = getFieldValue(row, ["标准接口字段名", "Standard Interface Field"]);
      if (!field || field === "-") continue;
      specRows.push({
        section: table.heading,
        group: sectionBucket(table.heading),
        field,
        rawField: getFieldValue(row, ["Newrez 原始字段", "Newrez Raw Field"]),
        type: getFieldValue(row, ["类型", "Type"]),
        priority: getFieldValue(row, ["优先级", "Priority"]) || priorityOf(row),
        format: getFieldValue(row, ["格式要求", "允许值/格式", "Format", "Allowed Values / Format"]),
        bpsFunction: getFieldValue(row, ["喂入的 BPS 面板/功能", "BPS 系统功能", "BPS Panel / Function", "BPS System Function", "BPS Panel / Field"]),
        newrezStatus: getFieldValue(row, ["Newrez 现状", "Newrez Status"]),
      });
    }
  }

  return specRows.map((row, idx) => {
    const meaning = meaningByField.get(row.field) || "";
    const panel = primaryPanel(`${row.bpsFunction} ${meaning}`, row.section);
    const status = statusCategory(row.newrezStatus);
    const needsReview = /Missing|Partial/.test(status) || /确认|待|是否|需/.test(`${row.bpsFunction} ${meaning} ${row.newrezStatus}`);
    const missingImpact =
      row.priority.includes("P0") ? "阻断入库或核心识别，需优先确认"
        : row.priority.includes("P1") ? "核心面板可能空白或计算不准"
          : row.priority.includes("P2") ? "增强分析受限，不阻断主流程"
            : "需结合具体面板确认";
    return {
      no: idx + 1,
      ...row,
      fullRawField: fullDbFieldPath(row.section, row.field, row.rawField),
      priority: normalizePriority(row.priority) || priorityOf(row),
      panel,
      meaning,
      statusCategory: status,
      missingImpact,
      reviewDecision: needsReview ? "待评审" : "可接受",
      reviewerComment: "",
    };
  });
}

function findQuestionRows(tables) {
  const rows = [];
  for (const table of tables) {
    if (!table.headers.some((h) => h === "问题")) continue;
    for (const row of table.rows) {
      rows.push({
        topic: row["问题"] || "",
        currentHandling: row["当前处理方式"] || "",
        nextAction: row["后续动作"] || "",
        sql: row["验证 SQL"] || "",
      });
    }
  }
  return rows;
}

function findTerms(tables) {
  const terms = [];
  for (const table of tables) {
    if (!table.headers.includes("术语 / 缩写")) continue;
    for (const row of table.rows) {
      terms.push({
        term: row["术语 / 缩写"],
        full: row["全称"],
        desc: row["说明"],
      });
    }
  }
  return terms;
}

function safeSheetName(name) {
  return name.slice(0, 31).replace(/[\\/?*\[\]:]/g, " ");
}

function colLetter(n) {
  let s = "";
  while (n > 0) {
    const m = (n - 1) % 26;
    s = String.fromCharCode(65 + m) + s;
    n = Math.floor((n - 1) / 26);
  }
  return s;
}

function writeMatrix(sheet, startRow, startCol, matrix) {
  if (!matrix.length) return null;
  const range = sheet.getRangeByIndexes(startRow, startCol, matrix.length, matrix[0].length);
  range.values = matrix;
  return range;
}

function styleTitle(sheet, rangeAddress, title, subtitle = "") {
  const range = sheet.getRange(rangeAddress);
  range.format.fill = { color: "#12355B" };
  range.format.font = { color: "#FFFFFF", size: 11 };
  range.format.wrapText = true;
  range.format.horizontalAlignment = "left";
  range.format.verticalAlignment = "center";
  range.format.rowHeightPx = 30;
  range.getCell(0, 0).values = [[title]];
  range.getCell(0, 0).format.font = { bold: true, color: "#FFFFFF", size: 16 };
  if (subtitle) {
    range.getCell(1, 0).values = [[subtitle]];
    range.getCell(1, 0).format.font = { color: "#FFFFFF", size: 10 };
  }
}

function styleTable(sheet, tableRangeAddress, tableName, headerRows = 1) {
  const range = sheet.getRange(tableRangeAddress);
  range.format.font = { size: 10, color: "#243447" };
  range.format.wrapText = true;
  range.format.verticalAlignment = "top";
  range.format.borders = {
    insideHorizontal: { style: "continuous", color: "#D8E1EA" },
    insideVertical: { style: "continuous", color: "#E7EDF3" },
    edgeBottom: { style: "continuous", color: "#B7C7D8" },
    edgeTop: { style: "continuous", color: "#B7C7D8" },
    edgeLeft: { style: "continuous", color: "#B7C7D8" },
    edgeRight: { style: "continuous", color: "#B7C7D8" },
  };
  const header = range.getRow(0);
  header.format.fill = { color: "#2E5E8C" };
  header.format.font = { bold: true, color: "#FFFFFF", size: 10 };
  header.format.verticalAlignment = "center";
  header.format.rowHeightPx = 34;
  try {
    const table = sheet.tables.add(tableRangeAddress, true, tableName);
    table.style = "TableStyleMedium2";
    table.showFilterButton = true;
  } catch {
    // Table creation is a presentation enhancement; the workbook remains usable without it.
  }
  if (headerRows > 0) sheet.freezePanes.freezeRows(headerRows + 2);
}

function setColumnWidths(sheet, widths) {
  widths.forEach((width, idx) => {
    sheet.getRange(`${colLetter(idx + 1)}:${colLetter(idx + 1)}`).format.columnWidthPx = width;
  });
}

function applyPriorityFormatting(sheet, rangeAddress, priorityColLetter, statusColLetter, decisionColLetter) {
  const range = sheet.getRange(rangeAddress);
  range.conditionalFormats.add("containsText", {
    text: "P0",
    format: { fill: { color: "#FCE4D6" }, font: { bold: true, color: "#8A2C0D" } },
  });
  sheet.getRange(`${priorityColLetter}:${priorityColLetter}`).conditionalFormats.add("containsText", {
    text: "P1",
    format: { fill: { color: "#FFF2CC" }, font: { bold: true, color: "#6B4E00" } },
  });
  sheet.getRange(`${priorityColLetter}:${priorityColLetter}`).conditionalFormats.add("containsText", {
    text: "P2",
    format: { fill: { color: "#E2F0D9" }, font: { color: "#275317" } },
  });
  sheet.getRange(`${statusColLetter}:${statusColLetter}`).conditionalFormats.add("containsText", {
    text: "Missing",
    format: { fill: { color: "#F8CBAD" }, font: { bold: true, color: "#7F1D1D" } },
  });
  sheet.getRange(`${statusColLetter}:${statusColLetter}`).conditionalFormats.add("containsText", {
    text: "Partial",
    format: { fill: { color: "#FCE4D6" }, font: { color: "#7C3A00" } },
  });
  sheet.getRange(`${statusColLetter}:${statusColLetter}`).conditionalFormats.add("containsText", {
    text: "Provided",
    format: { fill: { color: "#D9EAD3" }, font: { color: "#22543D" } },
  });
  sheet.getRange(`${decisionColLetter}:${decisionColLetter}`).dataValidation = {
    rule: { type: "list", values: ["待评审", "可接受", "需补充", "不适用", "需技术确认"] },
  };
}

function makeOverviewSheet(workbook, fieldRows, questions, terms) {
  const sheet = workbook.worksheets.add("00 使用指南");
  sheet.showGridLines = false;
  styleTitle(sheet, "A1:J2", "Doc 14 - Servicer FCL 数据接口业务评审包", "面向业务评审：先理解字段用途，再判断是否必须提供、是否需要补充说明");
  const counts = {
    total: fieldRows.length,
    p0: fieldRows.filter((r) => r.priority === "P0").length,
    p1: fieldRows.filter((r) => r.priority === "P1").length,
    p2: fieldRows.filter((r) => r.priority === "P2").length,
    missing: fieldRows.filter((r) => r.statusCategory === "Missing").length,
    partial: fieldRows.filter((r) => r.statusCategory === "Partial").length,
  };
  const cards = [
    ["字段总数", counts.total, "来自 Doc 14 字段规范表"],
    ["P0 必填", counts.p0, "入库或核心识别前提"],
    ["P1 核心展示", counts.p1, "影响 BPS 面板可用性"],
    ["P2 增强字段", counts.p2, "增强分析或补充合规"],
    ["缺失字段", counts.missing, "Newrez benchmark 未提供"],
    ["部分提供", counts.partial, "填充率低或需映射确认"],
  ];
  writeMatrix(sheet, 3, 0, cards);
  sheet.getRange("A4:C9").format.fill = { color: "#F7FAFC" };
  sheet.getRange("A4:A9").format.font = { bold: true, color: "#12355B" };
  sheet.getRange("B4:B9").format.font = { bold: true, size: 18, color: "#2E5E8C" };
  sheet.getRange("A4:C9").format.borders = {
    insideHorizontal: { style: "continuous", color: "#D8E1EA" },
    edgeBottom: { style: "continuous", color: "#B7C7D8" },
    edgeTop: { style: "continuous", color: "#B7C7D8" },
    edgeLeft: { style: "continuous", color: "#B7C7D8" },
    edgeRight: { style: "continuous", color: "#B7C7D8" },
  };

  const workflow = [
    ["评审步骤", "业务人员建议动作"],
    ["1. 先看 03_P0必填清单", "确认 Servicer 是否能提供入库前提字段，例如 loan_id、data_as_of_date、state、fcl_referral_date。"],
    ["2. 再看 02_按BPS面板", "按页面体验核对字段：Timeline、Summary、Hold、LM、BK、Aggregate 视图。"],
    ["3. 最后看 04_缺口与问题", "针对 Missing / Partial 字段给出是否必须补、是否可接受替代字段、是否需要产品确认。"],
    ["4. 在 Review Decision 写结论", "下拉选择：待评审、可接受、需补充、不适用、需技术确认。"],
  ];
  writeMatrix(sheet, 3, 4, workflow);
  styleTable(sheet, "E4:J8", "ReviewWorkflow", 0);
  sheet.getRange("E4:J4").format.fill = { color: "#4C7A91" };

  const legend = [
    ["优先级", "业务解释", "缺失影响"],
    ["P0", "系统入库或状态识别前提", "缺失会阻断收录或核心流程"],
    ["P1", "BPS 核心面板展示字段", "缺失会导致页面空白、天数或阶段判断不准"],
    ["P2", "增强分析/补充合规字段", "不阻断主流程，但会降低分析深度"],
  ];
  writeMatrix(sheet, 11, 0, legend);
  styleTable(sheet, "A12:D15", "PriorityLegend", 0);

  const sourceNotes = [
    ["来源", "用途"],
    ["Doc 14", "本工作簿主源：Servicer FCL 数据接口标准、字段优先级、业务含义、Newrez合规状态"],
    ["Doc 13", "参考源：BPS展示字段到Newrez原始字段的反向映射、术语、填充率和已知问题"],
    ["生成日期", today],
  ];
  writeMatrix(sheet, 11, 5, sourceNotes);
  styleTable(sheet, "F12:J15", "SourceNotes", 0);

  setColumnWidths(sheet, [120, 88, 280, 24, 120, 180, 180, 180, 180, 180]);
  sheet.getRange("A1:J30").format.wrapText = true;
  return sheet;
}

function makeFieldDictionary(workbook, fieldRows) {
  const sheet = workbook.worksheets.add("01 字段字典");
  sheet.showGridLines = false;
  styleTitle(sheet, "A1:L2", "字段规范 - 一行一个 Servicer FCL 接口字段", "按业务评审列设计；Newrez 原始字段使用 db.schema.table.field 完整路径，便于技术人员精准定位");
  const headers = [
    "#", "字段组", "标准接口字段", "Newrez原始字段（完整路径）", "数据类型", "优先级", "业务含义",
    "格式/计算规则", "BPS面板/功能", "Newrez状态", "Review Decision", "Reviewer Comment",
  ];
  const data = fieldRows.map((r) => [
    r.no, r.group, r.field, r.fullRawField, r.type, r.priority, r.meaning,
    r.format, r.bpsFunction || r.panel, r.newrezStatus, r.reviewDecision, r.reviewerComment,
  ]);
  writeMatrix(sheet, 3, 0, [headers, ...data]);
  const lastRow = 4 + data.length;
  styleTable(sheet, `A4:L${lastRow}`, "FieldDictionary", 3);
  applyPriorityFormatting(sheet, `A4:L${lastRow}`, "F", "J", "K");
  setColumnWidths(sheet, [48, 175, 210, 310, 105, 70, 430, 250, 300, 240, 130, 240]);
  sheet.freezePanes.freezeRows(4);
  sheet.freezePanes.freezeColumns(3);
  return sheet;
}

function makePanelSheet(workbook, fieldRows) {
  const sheet = workbook.worksheets.add("02 按BPS面板");
  sheet.showGridLines = false;
  styleTitle(sheet, "A1:K2", "按 BPS 面板评审", "用页面视角理解字段：业务人员可按自己负责的面板过滤查看");
  const headers = ["BPS面板", "字段组", "标准接口字段名", "业务含义", "优先级", "Newrez字段", "Newrez状态", "缺失影响", "Review Decision", "Reviewer", "Comment"];
  const sorted = [...fieldRows].sort((a, b) => `${a.panel}${a.group}${a.no}`.localeCompare(`${b.panel}${b.group}${b.no}`, "zh"));
  const data = sorted.map((r) => [r.panel, r.group, r.field, r.meaning, r.priority, r.fullRawField, r.newrezStatus, r.missingImpact, r.reviewDecision, "", ""]);
  writeMatrix(sheet, 3, 0, [headers, ...data]);
  const lastRow = 4 + data.length;
  styleTable(sheet, `A4:K${lastRow}`, "PanelReview", 3);
  applyPriorityFormatting(sheet, `A4:K${lastRow}`, "E", "G", "I");
  setColumnWidths(sheet, [180, 160, 200, 440, 70, 220, 220, 220, 125, 110, 240]);
  sheet.freezePanes.freezeRows(4);
  sheet.freezePanes.freezeColumns(3);
  return sheet;
}

function makeP0Sheet(workbook, fieldRows) {
  const sheet = workbook.worksheets.add("03 P0必填清单");
  sheet.showGridLines = false;
  styleTitle(sheet, "A1:J2", "P0 必填字段 - Servicer 接入最低门槛", "这些字段用于入库、贷款识别、状态识别或核心 FCL 路由；建议优先完成业务确认");
  const rows = fieldRows.filter((r) => r.priority === "P0");
  const headers = ["字段组", "标准接口字段名", "业务含义", "格式/允许值", "Newrez原始字段", "BPS功能", "Newrez现状", "缺失影响", "Review Decision", "Comment"];
  const data = rows.map((r) => [r.group, r.field, r.meaning, r.format, r.fullRawField, r.bpsFunction, r.newrezStatus, r.missingImpact, r.reviewDecision, ""]);
  writeMatrix(sheet, 3, 0, [headers, ...data]);
  const lastRow = 4 + data.length;
  styleTable(sheet, `A4:J${lastRow}`, "P0Review", 3);
  applyPriorityFormatting(sheet, `A4:J${lastRow}`, "A", "G", "I");
  setColumnWidths(sheet, [160, 210, 430, 220, 220, 260, 230, 230, 130, 240]);
  return sheet;
}

function makeGapsSheet(workbook, fieldRows, questions) {
  const sheet = workbook.worksheets.add("04 缺口与问题");
  sheet.showGridLines = false;
  styleTitle(sheet, "A1:K2", "缺口与待确认问题", "Missing / Partial 字段和 Doc 14 开放问题集中在这里，便于会议逐项过");
  const gaps = fieldRows.filter((r) => ["Missing", "Partial"].includes(r.statusCategory));
  const gapHeaders = ["类型", "字段组", "标准接口字段名", "业务含义", "优先级", "Newrez原始字段", "Newrez现状", "建议评审问题", "Review Decision", "Owner", "Comment"];
  const gapData = gaps.map((r) => [
    r.statusCategory, r.group, r.field, r.meaning, r.priority, r.fullRawField, r.newrezStatus,
    r.statusCategory === "Missing" ? "是否必须向新 Servicer 明确要求？是否接受替代字段/内部推导？" : "填充率或映射是否满足业务使用？是否需要设为硬性要求？",
    r.reviewDecision, "", "",
  ]);
  writeMatrix(sheet, 3, 0, [gapHeaders, ...gapData]);
  let lastRow = 4 + gapData.length;
  styleTable(sheet, `A4:K${lastRow}`, "GapReview", 3);
  applyPriorityFormatting(sheet, `A4:K${lastRow}`, "E", "A", "I");
  const qStart = lastRow + 3;
  writeMatrix(sheet, qStart - 1, 0, [["Doc 14 开放问题", "当前处理方式", "后续动作", "验证 SQL / 依据", "会议结论"]]);
  writeMatrix(sheet, qStart, 0, questions.map((q) => [q.topic, q.currentHandling, q.nextAction, q.sql, ""]));
  const qEnd = qStart + Math.max(questions.length, 1);
  styleTable(sheet, `A${qStart}:E${qEnd}`, "OpenQuestions", 0);
  setColumnWidths(sheet, [130, 150, 210, 420, 70, 210, 240, 280, 130, 110, 240]);
  return sheet;
}

function makeSourcesSheet(workbook, terms) {
  const sheet = workbook.worksheets.add("05 来源与术语");
  sheet.showGridLines = false;
  styleTitle(sheet, "A1:H2", "来源、术语与评审边界", "保留业务评审所需的上下文，避免每次回查 Markdown");
  const docs = [
    ["文档", "角色", "路径", "备注"],
    ["Doc 14", "主源", "docs/zh/14_bps_driven_servicer_fcl_interface.md", "字段标准、优先级、业务含义、Newrez现状"],
    ["Doc 13", "参考源", "docs/zh/13_newrez_fcl_bps_display_mapping.md", "BPS展示字段反向映射、术语、实测填充率、已知问题"],
    ["Doc 09", "上游标准", "docs/zh/09_servicer_data_interface_standard.md", "行业标准字段、P0/P1/P2口径"],
    ["Doc 12", "链路参考", "docs/zh/12_sync_asset_management.md", "ETL中间层和BPS同步细节"],
  ];
  writeMatrix(sheet, 3, 0, docs);
  styleTable(sheet, "A4:D8", "DocumentSources", 3);
  const termHeaders = ["术语 / 缩写", "全称", "说明"];
  const termData = terms.map((t) => [t.term, t.full, t.desc]);
  writeMatrix(sheet, 10, 0, [termHeaders, ...termData]);
  const termEnd = 11 + termData.length;
  styleTable(sheet, `A11:C${termEnd}`, "Terms", 0);
  setColumnWidths(sheet, [190, 210, 620, 260, 120, 120, 120, 120]);
  return sheet;
}

const zh14 = await fs.readFile(zh14Path, "utf8");
const zh13 = await fs.readFile(zh13Path, "utf8");
const doc14Tables = readTables(zh14);
const doc13Tables = readTables(zh13);
const fieldRows = buildFieldRows(doc14Tables);
const questions = findQuestionRows(doc14Tables);
const terms = findTerms(doc13Tables);

const workbook = Workbook.create();
makeOverviewSheet(workbook, fieldRows, questions, terms);
makeFieldDictionary(workbook, fieldRows);
makePanelSheet(workbook, fieldRows);
makeP0Sheet(workbook, fieldRows);
makeGapsSheet(workbook, fieldRows, questions);
makeSourcesSheet(workbook, terms);

for (const sheet of workbook.worksheets.items ?? []) {
  try {
    const usedRange = sheet.getUsedRange();
    if (usedRange) {
      usedRange.format.wrapText = true;
      usedRange.format.verticalAlignment = "top";
    }
  } catch {
    // Best-effort styling; some ranges may be empty during recovery.
  }
}

await fs.mkdir(outputDir, { recursive: true });

const summary = {
  fieldCount: fieldRows.length,
  p0: fieldRows.filter((r) => r.priority === "P0").length,
  p1: fieldRows.filter((r) => r.priority === "P1").length,
  p2: fieldRows.filter((r) => r.priority === "P2").length,
  missing: fieldRows.filter((r) => r.statusCategory === "Missing").length,
  partial: fieldRows.filter((r) => r.statusCategory === "Partial").length,
  questions: questions.length,
  terms: terms.length,
};

const preview = await workbook.render({ sheetName: "00 使用指南", autoCrop: "all", scale: 1, format: "png" });
await fs.writeFile(path.join(outputDir, "preview_00_review_guide.png"), new Uint8Array(await preview.arrayBuffer()));
const fieldPreview = await workbook.render({ sheetName: "01 字段字典", range: "A1:L22", scale: 1, format: "png" });
await fs.writeFile(path.join(outputDir, "preview_01_field_dictionary.png"), new Uint8Array(await fieldPreview.arrayBuffer()));

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "formula error scan",
});

const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(outputPath);

console.log(JSON.stringify({ outputPath, summary, errors: errors.ndjson ?? "" }, null, 2));
