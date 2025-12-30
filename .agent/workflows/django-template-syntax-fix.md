---
description: Django Template Syntax Error - Comparison Operators
---

# Django Template Syntax Errors - Quick Reference

## Error 1: Missing Spaces Around Operators

### Common Error Message
```
TemplateSyntaxError: Could not parse the remainder: '==selected_month' from 'm_num==selected_month'
```

### Wrong ❌
```django
{% if m_num==selected_month %}  {# Missing spaces #}
{% if y==selected_year %}
{% if count>0 %}
```

### Correct ✅
```django
{% if m_num == selected_month %}  {# Spaces required #}
{% if y == selected_year %}
{% if count > 0 %}
```

### Fix Command
```bash
perl -i -pe 's/==(\w)/ == $1/g; s/(\w)==/$1 ==/g' templates/**/*.html
```

---

## Error 2: Broken/Split Template Tags

### Common Error Message
```
TemplateSyntaxError: Invalid block tag on line X: 'empty', expected 'elif', 'else' or 'endif'
```

### Wrong ❌
```django
{% if condition %}<span>text</span>{%
                endif %}   {# Tag split across lines #}
```

### Correct ✅
```django
{% if condition %}<span>text</span>{% endif %}  {# Tag on single line #}
```

### Fix Command
```bash
perl -i -0pe 's/\{%\s*\n\s*endif\s*%\}/{% endif %}/g' templates/**/*.html
```

---

## Prevention Tips
1. **Always use spaces** around operators: `==`, `!=`, `<`, `>`, `and`, `or`, `not`
2. **Never split template tags** across lines - keep `{% ... %}` on one line
3. **Use lint/check tools** before committing template changes

---

## ⚠️ CRITICAL: Always Verify After Fixing

> [!CAUTION]
> The `replace_file_content` tool may report success but fail to persist changes.
> **ALWAYS verify with sed/cat after EVERY edit before testing in browser.**

```bash
# After any fix, verify the actual file content:
sed -n '25p;34p' attendance/templates/attendance/report.html

# Use Python for reliable multi-line fixes:
python3 << 'EOF'
with open('file.html', 'r') as f:
    content = f.read()
content = content.replace('old', 'new')
with open('file.html', 'w') as f:
    f.write(content)
EOF
```

## Affected Files (This Project)
- `attendance/templates/attendance/report.html` - Uses include for filters
- `attendance/templates/attendance/includes/report_filters.html` - **PROTECTED FILE** - Filter component with correct syntax

## ✅ PERMANENT SOLUTION: Template Includes

To prevent this issue from recurring, the filter dropdowns have been moved to a separate include file:

```
attendance/templates/attendance/includes/report_filters.html
```

This is included in `report.html` with:
```django
{% include 'attendance/includes/report_filters.html' %}
```

**Benefits:**
1. Less likely to be accidentally modified when editing report.html
2. Reusable across multiple report pages
3. Contains warning comment at the top
4. Single source of truth for filter syntax
