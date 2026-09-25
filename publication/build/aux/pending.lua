
-- Highlight spans with class "pending" in LaTeX output (HTML uses CSS).
function Span(el)
  if el.classes:includes("pending") and FORMAT:match("latex") then
    local out = { pandoc.RawInline("latex", "\\textcolor{red}{\\textbf{") }
    for _, x in ipairs(el.content) do table.insert(out, x) end
    table.insert(out, pandoc.RawInline("latex", "}}"))
    return out
  end
end
