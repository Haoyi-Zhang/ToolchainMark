#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / 'paper'
ARTIFACT = ROOT / 'artifact'
TEX = PAPER / 'main.tex'
BIB = PAPER / 'references.bib'
RECORDS = PAPER / 'evidence' / 'reference_records.json'
RECEIPTS = ARTIFACT / 'evidence' / 'reference_review_current.json'
COMPANION_RECEIPTS = ARTIFACT / 'evidence' / 'reference_review_companion.json'
LEDGER = ARTIFACT / 'citation_support.csv'
SHAPE = PAPER / 'citation_shape_audit.json'
VERIFY = PAPER / 'reference_verification_audit.json'
LINE_AUDIT = PAPER / 'reference_line_by_line_audit.csv'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_receipts():
    """Use companion evidence only for the bibliography bytes it binds."""
    if COMPANION_RECEIPTS.is_file():
        companion = json.loads(COMPANION_RECEIPTS.read_text(encoding='utf-8'))
        if not isinstance(companion, dict) or not isinstance(companion.get('receipts'), list):
            raise ValueError('Malformed companion reference receipt')
        identity = companion.get('bibliography_sha256')
        if not isinstance(identity, str) or not re.fullmatch(r'[0-9a-f]{64}', identity):
            raise ValueError('Missing or invalid companion bibliography binding')
        if identity == sha256(BIB):
            return COMPANION_RECEIPTS, companion['receipts']
    return RECEIPTS, json.loads(RECEIPTS.read_text(encoding='utf-8'))


def strip_tex(text: str) -> str:
    text = re.sub(r'%.*', '', text)
    text = re.sub(r'\\cite\{[^}]+\}', '', text)
    text = re.sub(r'\\(?:textsc|emph|textit|textbf|texttt|mathrm|mathsf)\{([^{}]*)\}', r'\1', text)
    text = re.sub(r'\\(?:mr|suite)\{([^{}]*)\}', r'\1', text)
    text = re.sub(r'\\[A-Za-z@]+\*?(?:\[[^\]]*\])?', '', text)
    text = text.replace('~', ' ')
    text = text.replace('``', '"').replace("''", '"')
    text = text.replace('--', '-')
    text = re.sub(r'[{}$]', '', text)
    text = re.sub(r'\\([%&_#])', r'\1', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_bib(text: str) -> dict[str, dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}
    for match in re.finditer(r'@(\w+)\{([^,]+),\s*(.*?)\n\}', text, re.S):
        entry_type, key, body = match.group(1).lower(), match.group(2).strip(), match.group(3)
        if key in entries:
            raise ValueError('Duplicate BibTeX key: ' + key)
        fields: dict[str, str] = {'entry_type': entry_type}
        for fm in re.finditer(r'^\s*(\w+)\s*=\s*\{(.*?)\}\s*,?\s*$', body, re.M | re.S):
            field = fm.group(1).lower()
            if field in fields:
                raise ValueError('Duplicate BibTeX field for ' + key + ': ' + field)
            fields[field] = fm.group(2).strip()
        entries[key] = fields
    return entries


def normalize_people(value: str) -> str:
    value = strip_tex(value).lower()
    value = value.replace(' and ', ' ')
    return ''.join(c for c in unicodedata.normalize('NFKD', value).casefold() if c.isalnum())


def scholarly_identifier(record: dict) -> str:
    """Identify a work, not its claim support; reject absent/ambiguous identities."""
    doi = record.get('doi', '')
    repository = record.get('primary_repository', '')
    if not isinstance(doi, str) or not isinstance(repository, str):
        raise ValueError('Identifiers must be strings')
    doi, repository = doi.strip(), repository.strip().rstrip('/')
    if bool(doi) == bool(repository):
        raise ValueError('Require exactly one DOI or primary repository identifier')
    if doi:
        if not re.fullmatch(r'10\.[0-9]{4,9}/[^\s]+', doi):
            raise ValueError('Expected a bare DOI of the form 10.<registrant>/<suffix>')
        return 'doi:' + doi.casefold()
    if not re.fullmatch(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        raise ValueError('Expected a primary GitHub repository root URL')
    return 'repository:' + repository.removeprefix('https://').casefold()


def record_matches_bib(record: dict, fields: dict) -> bool:
    """Local metadata correspondence only, never a body-support verdict."""
    def norm(value):
        return re.sub(r'[^a-z0-9]', '', strip_tex(str(value)).lower())
    try:
        identity = scholarly_identifier(record)
        if norm(fields.get('title', '')) != norm(record['title']):
            return False
        if identity.startswith('doi:'):
            return (fields.get('doi', '').casefold() == record['doi'].casefold()
                    and normalize_people(fields.get('author', '')) == normalize_people(record['authors'])
                    and str(fields.get('year', '')) == str(record.get('year', '')))
        return (not fields.get('doi') and
                fields.get('url', '').rstrip('/').casefold() == record['primary_repository'].rstrip('/').casefold()
                and normalize_people(fields.get('author', '')) == normalize_people(record['authors'])
                and str(fields.get('year', '')) == str(record.get('year', '')))
    except (KeyError, TypeError, ValueError):
        return False


def validate_reference_inputs(records: list, receipts: list) -> None:
    """Shared consumer schema; declarations are not independent support proof."""
    if not isinstance(records, list) or not records or not isinstance(receipts, list) or not receipts:
        raise ValueError('Require nonempty reference and receipt lists')
    def required_text(row, names, kind):
        if not isinstance(row, dict):
            raise ValueError(kind + ' must be an object')
        for name in names:
            value = row.get(name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(kind + ' requires nonempty text: ' + name)
    for row in records:
        required_text(row, ('citation_key', 'title', 'authors'), 'Reference')
        if type(row.get('number')) is not int or row['number'] <= 0:
            raise ValueError('Reference number must be a positive integer')
        identity = scholarly_identifier(row)
        year = row.get('year', '')
        if type(year) not in (int, str):
            raise ValueError('Reference year must be text or an integer, not a Boolean')
        if identity.startswith('doi:') and not re.fullmatch(r'[1-9][0-9]{3}', str(year)):
            raise ValueError('DOI reference year must be a four-digit year')
    for row in receipts:
        required_text(row, ('citation_key', 'locator', 'source_class', 'verification_scope'), 'Receipt')
        if type(row.get('record_located_this_revision')) is not bool:
            raise ValueError('Receipt location declaration must be a Boolean')
        for name in ('full_text_reviewed', 'inherited_record_located'):
            if name in row and type(row[name]) is not bool:
                raise ValueError('Receipt ' + name + ' must be a Boolean')
        if 'body_reading_locations' in row and not isinstance(row['body_reading_locations'], list):
            raise ValueError('Receipt body_reading_locations must be a list of scoped records')
        scholarly_identifier(row)


def structural_audit(tex: str, bib: dict, records: list, receipts: list) -> dict:
    if any(type(row.get('record_located_this_revision')) is not bool for row in receipts):
        raise ValueError('Receipt location declaration must be a Boolean')
    commands=re.findall(r'\\cite\{([^}]+)\}',tex)
    sentences = re.split(r'(?<=[.!?])\s+', re.sub(r'(?m)^\s*%.*$', '', tex))
    multiple = [sentence for sentence in sentences if len(re.findall(r'\\cite\{', sentence)) > 1]
    keys=[k.strip() for c in commands for k in c.split(',')]
    rk={r['citation_key'] for r in records}; bk=set(bib)
    doi=[r['doi'].casefold() for r in records if r.get('doi')]
    identifiers=[]; identifier_errors=[]; receipt_identifier_mismatches=[]
    for record in records:
        try: identifiers.append(scholarly_identifier(record))
        except ValueError as error: identifier_errors.append({'key':record.get('citation_key'), 'error':str(error)})
    byrecord={r['citation_key']:r for r in records}
    for receipt in receipts:
        key=receipt['citation_key']
        try:
            if key not in byrecord or scholarly_identifier(receipt)!=scholarly_identifier(byrecord[key]):
                receipt_identifier_mismatches.append(key)
        except ValueError: receipt_identifier_mismatches.append(key)
    return {'record_count':len(records),'citation_commands':len(commands),'unique_citation_keys':len(set(keys)),
      'multi_key_commands':sum(',' in c for c in commands),
      'adjacent_citation_piles':len(re.findall(r'\\cite\{[^}]+\}\s*\\cite\{[^}]+\}',tex)),
      'uncited_bibliography_keys':sorted(bk-set(keys)),'missing_bibliography_keys':sorted(set(keys)-bk),
      'metadata_record_keys_match':rk==bk,'doi_records_unique':len(doi)==len(set(doi)),
      'record_keys_unique':len(records)==len(rk),
      'receipt_keys_match':{r['citation_key'] for r in receipts}==rk,
      'identifier_errors':identifier_errors,
      'receipt_identifier_mismatches':receipt_identifier_mismatches,
      'scholarly_identifiers_unique':not identifier_errors and len(identifiers)==len(set(identifiers)),
      'doi_record_count':len(doi),'primary_repository_record_count':sum(bool(r.get('primary_repository')) for r in records),
      'receipt_keys_unique':len(receipts)==len({r['citation_key'] for r in receipts}),
      'fresh_record_checks':sum(bool(r['record_located_this_revision']) for r in receipts),
      'sentences_with_multiple_citation_commands':len(multiple),
      'multiple_citation_sentence_examples':multiple[:4],
      'numeric_citation_ranges':len(re.findall(r'\\cite\{[^}]*\d\s*[-–]\s*\d[^}]*\}', tex)),
      'full_text_review_claimed':False}

def main() -> None:
    tex=TEX.read_text(encoding='utf-8'); bib=parse_bib(BIB.read_text(encoding='utf-8')); records=json.loads(RECORDS.read_text(encoding='utf-8'))
    receipt_path,receipts=load_receipts()
    validate_reference_inputs(records, receipts)
    byreceipt={r['citation_key']:r for r in receipts}; shape=structural_audit(tex,bib,records,receipts)
    if not (shape['record_keys_unique'] and shape['receipt_keys_unique'] and shape['receipt_keys_match']):
        raise ValueError('Current records and receipts require unique matching keys')
    if shape['identifier_errors'] or shape['receipt_identifier_mismatches']:
        raise ValueError('Invalid or mismatched scholarly identifiers')
    citations=[]; section=''; subsection=''
    for lineno,line in enumerate(tex.splitlines(),1):
        m=re.match(r'\\section\{([^}]+)\}',line)
        if m: section=m.group(1);subsection=''
        m=re.match(r'\\subsection\{([^}]+)\}',line)
        if m:subsection=m.group(1)
        for m in re.finditer(r'\\cite\{([^}]+)\}',line):
            left=max(line.rfind('. ',0,m.start()),line.rfind('? ',0,m.start()))
            left=left+2 if left>=0 else 0
            ends=[x for x in [line.find('. ',m.end()),line.find('? ',m.end())] if x>=0]
            right=min(ends)+1 if ends else len(line)
            for key in m.group(1).split(','):
                citations.append({'key':key.strip(),'line':lineno,'section':section,'subsection':subsection,'sentence':strip_tex(line[left:right])})
    audit=[];ledger=[];local_mismatches=[]
    for rec in records:
        key=rec['citation_key']; b=bib.get(key,{}); rr=byreceipt[key]; cs=[c for c in citations if c['key']==key]
        match=record_matches_bib(rec,b)
        if not match:local_mismatches.append(key)
        location='; '.join(f"{c['section']} / {c['subsection']}, line {c['line']}" for c in cs)
        context=' || '.join(c['sentence'] for c in cs)
        status='RECORD_LOCATED_SCOPE_LIMITED' if rr['record_located_this_revision'] else 'INHERITED_NOT_FRESHLY_VERIFIED'
        body_status='SCOPED_PRIMARY_BODY_READING_RECORDED_NOT_AUTOMATICALLY_CERTIFIED' if rr.get('body_reading_locations') else 'CLAIM_CONTEXT_RETAINED_NOT_AUTOMATICALLY_PROVEN'
        audit.append({'reference_number':rec['number'],'citation_key':key,'title':rec['title'],'authors':rec['authors'],'year':rec.get('year',''),'doi':rec.get('doi',''),'scholarly_identifier':scholarly_identifier(rec),'source_locator':rr['locator'],'source_class':rr['source_class'],'local_record_consistency':'PASS' if match else 'FAIL','external_review_status':status,'verification_scope':rr['verification_scope'],'manuscript_location':location,'local_claims':context,'support_status':body_status,'full_text_reviewed':False})
        evidence={'reference':rec,'receipt':rr,'contexts':cs}
        ledger.append({'citation_key':key,'manuscript_location':location,'scholarly_identifier':scholarly_identifier(rec),'source_locator':rr['locator'],'support_paraphrase':context,'evidence_sha256':hashlib.sha256(json.dumps(evidence,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),'verification_status':status})
    if local_mismatches:
        raise ValueError('Local bibliographic metadata differs: ' + repr(local_mismatches))
    ledger_path=PAPER/'reference_support.csv' if receipt_path==COMPANION_RECEIPTS else LEDGER
    for path,rows in [(LINE_AUDIT,audit),(ledger_path,ledger)]:
        with path.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    shape['local_record_mismatches']=local_mismatches
    shape['structural_verdict']='PASS' if not(local_mismatches or shape['receipt_identifier_mismatches'] or shape['multi_key_commands'] or shape['adjacent_citation_piles'] or shape['sentences_with_multiple_citation_commands'] or shape['numeric_citation_ranges'] or shape['uncited_bibliography_keys'] or shape['missing_bibliography_keys']) and shape['metadata_record_keys_match'] and shape['record_keys_unique'] and shape['receipt_keys_unique'] and shape['receipt_keys_match'] and shape['scholarly_identifiers_unique'] else 'FAIL'
    SHAPE.write_text(json.dumps(shape,indent=2)+'\n',encoding='utf-8')
    report={'schema_version':'current-evidence-separated','record_count':len(records),'unique_scholarly_identifiers':len({scholarly_identifier(r) for r in records}),'doi_record_count':shape['doi_record_count'],'primary_repository_record_count':shape['primary_repository_record_count'],'current_receipts':receipt_path.relative_to(ROOT).as_posix(),'fresh_documented_record_checks':shape['fresh_record_checks'],'inherited_records_not_freshly_reverified':[r['citation_key'] for r in receipts if not r['record_located_this_revision']],'scoped_primary_body_reading_records':[r['citation_key'] for r in receipts if r.get('body_reading_locations')],'source_class_counts':dict(Counter(r['source_class'] for r in receipts)),'structural_verdict':shape['structural_verdict'],'semantic_verdict':'PARTIAL_EXTERNAL_REVIEW_NOT_FULL_TEXT_CERTIFICATION','verification_scope':'Structural bibliography/citation checks are automated. DOI and primary repository identifiers establish identity only. Scoped primary-body reading declarations are retained in current receipts, not independently certified by this script. Inherited receipts are not freshly reverified here. A citation occurrence, matching local record, or hash is not proof of claim support; no universal full-text certification is inferred.','imported_audits':'artifact/results/protocol-history/imported-audits','verdict':'PASS_STRUCTURAL_WITH_DISCLOSED_REVIEW_LIMITS' if shape['structural_verdict']=='PASS' else 'FAIL_STRUCTURAL'}
    VERIFY.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
    if shape['structural_verdict']!='PASS':raise SystemExit(1)

if __name__=='__main__':main()
