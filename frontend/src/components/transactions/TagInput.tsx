import { tagPillStyle } from "@/lib/tagColors";
import { X } from "lucide-react";
import { useRef, useState } from "react";

const MAX_TAGS = 10;
const MAX_TAG_LENGTH = 30;

interface TagInputProps {
  value: string[];
  onChange: (tags: string[]) => void;
  availableTags: string[];
  error?: string;
}

function validateTag(tag: string): string | null {
  if (/\s/.test(tag)) return "Tags cannot contain spaces";
  if (tag.length > MAX_TAG_LENGTH) return `Tags must be ${MAX_TAG_LENGTH} characters or fewer`;
  if (tag.length === 0) return null; // empty — just ignore
  return null;
}

export function TagInput({ value, onChange, availableTags, error }: TagInputProps) {
  const [inputValue, setInputValue] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const filteredSuggestions = availableTags.filter(
    (tag) =>
      tag.toLowerCase().includes(inputValue.toLowerCase()) &&
      !value.includes(tag),
  );

  function addTag(raw: string) {
    const tag = raw.trim().replace(/,/g, "");
    if (!tag) return;

    if (value.includes(tag)) {
      setInputValue("");
      return;
    }
    if (value.length >= MAX_TAGS) {
      setValidationError(`Maximum ${MAX_TAGS} tags allowed`);
      return;
    }
    const err = validateTag(tag);
    if (err) {
      setValidationError(err);
      return;
    }

    setValidationError(null);
    onChange([...value, tag]);
    setInputValue("");
  }

  function removeTag(tag: string) {
    onChange(value.filter((t) => t !== tag));
    setValidationError(null);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addTag(inputValue);
    } else if (e.key === "Backspace" && inputValue === "" && value.length > 0) {
      removeTag(value[value.length - 1]);
    }
  }

  const isAtLimit = value.length >= MAX_TAGS;
  const displayError = error ?? validationError;

  return (
    <div className="space-y-1">
      <div
        className={`min-h-8 w-full flex flex-wrap gap-1 items-center rounded-md border px-2 py-1 bg-background cursor-text ${displayError ? "border-destructive" : "border-input"} focus-within:ring-2 focus-within:ring-ring`}
        onClick={() => inputRef.current?.focus()}
      >
        {value.map((tag) => (
          <span
            key={tag}
            style={tagPillStyle(tag)}
            className="inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium"
          >
            {tag}
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); removeTag(tag); }}
              className="opacity-60 hover:opacity-100 transition-opacity"
              aria-label={`Remove tag ${tag}`}
            >
              <X size={10} />
            </button>
          </span>
        ))}
        {!isAtLimit && (
          <div className="relative flex-1 min-w-20">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => {
                setInputValue(e.target.value);
                setIsOpen(true);
                setValidationError(null);
              }}
              onKeyDown={handleKeyDown}
              onFocus={() => setIsOpen(true)}
              onBlur={() => setTimeout(() => setIsOpen(false), 150)}
              placeholder={value.length === 0 ? "Add tags…" : ""}
              className="w-full h-6 bg-transparent text-sm focus:outline-none placeholder:text-muted-foreground"
            />
            {isOpen && (inputValue || filteredSuggestions.length > 0) && filteredSuggestions.length > 0 && (
              <div className="absolute left-0 top-full mt-1 z-50 w-48 rounded-md border border-border bg-popover shadow-md">
                <ul className="py-1 max-h-40 overflow-y-auto">
                  {filteredSuggestions.map((tag) => (
                    <li key={tag}>
                      <button
                        type="button"
                        onMouseDown={(e) => { e.preventDefault(); addTag(tag); }}
                        className="w-full text-left px-3 py-1.5 text-sm hover:bg-accent transition-colors flex items-center gap-2"
                      >
                        <span
                          style={tagPillStyle(tag)}
                          className="inline-block rounded-full border px-2 py-0.5 text-xs font-medium"
                        >
                          {tag}
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
      <p className="text-xs text-muted-foreground">
        Press Enter or comma to add · No spaces · Max {MAX_TAG_LENGTH} chars · {value.length}/{MAX_TAGS} tags
      </p>
      {displayError && <p className="text-xs text-destructive">{displayError}</p>}
    </div>
  );
}
