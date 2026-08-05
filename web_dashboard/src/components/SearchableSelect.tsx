"use client";

import { useState, useRef, useEffect } from "react";
import { ChevronDown, Search, Check } from "lucide-react";

export interface Option {
  id: string;
  name: string;
  color?: string;
}

interface SearchableSelectProps {
  options: Option[];
  value: string;
  onChange: (id: string) => void;
  placeholder?: string;
  isRole?: boolean;
}

export default function SearchableSelect({ options, value, onChange, placeholder = "Chọn...", isRole = false }: SearchableSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filteredOptions = options.filter(opt => 
    opt.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const selectedOption = options.find(opt => opt.id === value);

  const getColorHex = (colorInt: string | undefined) => {
    if (!colorInt || colorInt === "0") return null;
    const hex = parseInt(colorInt).toString(16).padStart(6, '0');
    return `#${hex}`;
  };

  return (
    <div className="relative w-full" ref={wrapperRef}>
      <div 
        className="flex items-center justify-between w-full bg-surface border border-border text-sm rounded-lg px-3 py-2 text-white cursor-pointer hover:border-primary transition-colors"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center gap-2 overflow-hidden">
          {isRole && selectedOption && getColorHex(selectedOption.color) && (
            <div className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: getColorHex(selectedOption.color)! }} />
          )}
          <span className={`truncate ${selectedOption ? "text-white font-medium" : "text-text-muted"}`}>
            {selectedOption ? (isRole ? `@${selectedOption.name}` : `#${selectedOption.name}`) : placeholder}
          </span>
        </div>
        <ChevronDown className={`w-4 h-4 shrink-0 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </div>

      {isOpen && (
        <div className="absolute z-50 w-full mt-2 bg-surface border border-border rounded-lg shadow-xl overflow-hidden animate-fade-in">
          <div className="p-2 border-b border-border flex items-center gap-2">
            <Search className="w-4 h-4 text-text-muted shrink-0" />
            <input 
              type="text" 
              className="w-full bg-transparent border-none outline-none text-sm text-white placeholder-text-muted"
              placeholder="Tìm kiếm..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              autoFocus
            />
          </div>
          <div className="max-h-60 overflow-y-auto custom-scrollbar">
            {filteredOptions.length > 0 ? (
              filteredOptions.map((opt) => {
                const color = getColorHex(opt.color);
                return (
                  <div 
                    key={opt.id}
                    className={`px-3 py-2 text-sm cursor-pointer hover:bg-primary/20 flex items-center justify-between ${value === opt.id ? 'bg-primary/10 text-primary' : 'text-white'}`}
                    onClick={() => {
                      onChange(opt.id);
                      setIsOpen(false);
                      setSearchTerm("");
                    }}
                  >
                    <div className="flex items-center gap-2 truncate pr-2">
                      {isRole && color && (
                         <div className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: color }} />
                      )}
                      <span className="truncate">{isRole ? `@${opt.name}` : `#${opt.name}`}</span>
                    </div>
                    {value === opt.id && <Check className="w-4 h-4 shrink-0" />}
                  </div>
                );
              })
            ) : (
              <div className="px-3 py-4 text-sm text-center text-text-muted">Không tìm thấy kết quả</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
