---
name: contact-json
description: Extract contact information (name, address, phone) from user input and output it as JSON that is guaranteed valid. The output is verified by a bundled Python script using a pydantic model before being shown — if validation fails, the JSON is fixed and re-validated in a loop until it passes. Use this skill whenever the user provides a name/address/phone and asks for JSON output, structured contact data, or says things like "把姓名地址电话输出成JSON", "format this contact info as JSON", "extract my contact details", even if they don't explicitly mention validation.
---

# Contact Info → Validated JSON

Turn free-form contact info (姓名 / name, 地址 / address, 电话 / phone) into JSON that is
**provably valid** — never hand the user JSON that hasn't passed the validator.

## Why the validation loop matters

Hand-written JSON drifts: missing quotes, wrong keys, empty fields, malformed phone numbers.
The user relies on this output being machine-consumable, so the contract is: **only output
JSON after the validator has accepted it.** The pydantic model is the single source of truth
for what "correct" means — trust it over your own judgment of the format.

## Workflow

1. **Extract** the three fields from the user's input:
   - `name` — non-empty string, ≤100 chars
   - `address` — non-empty string, ≤300 chars
   - `phone` — digits plus optional `+ - ( ) .` and spaces, 5–25 chars, must contain a digit

   If any field is missing from the input, ask the user for it rather than inventing data.

2. **Draft the JSON** with exactly these keys:

   ```json
   {
     "name": "张三",
     "address": "北京市朝阳区xxx街1号",
     "phone": "+86 138-0000-0000"
   }
   ```

3. **Validate** by piping the draft into the bundled script:

   ```bash
   echo '<draft json>' | python3 <skill-dir>/scripts/validate_contact.py
   ```

   (Or write the draft to a temp file and pass the path as an argument.)

4. **Fix and re-validate**: if the script exits non-zero, read its error list — it names the
   field, the problem, and the offending value. Correct the JSON accordingly and run the
   validator again. Repeat until it prints `VALID` and exits 0. Common fixes:
   - JSON syntax errors → fix quotes/commas/braces
   - `phone` invalid → strip illegal characters (letters, `#`, `*`), keep digits and `+ - ( ) .`
   - empty/whitespace fields → go back to the user input; if truly absent, ask the user

5. **Output** the exact normalized JSON printed by the validator (after the `VALID` line) to
   the user. This guarantees the delivered output is byte-for-byte what the pydantic model
   accepted.

## Notes

- Requires Python 3 with `pydantic` (v2) installed.
- Non-ASCII text (e.g. Chinese names/addresses) is fully supported; output keeps original
  characters (`ensure_ascii=False`).
- Never skip step 3–4, even when the draft "looks right" — the validator is cheap and the
  guarantee is the whole point of this skill.
