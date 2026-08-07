"use client";

import { useState, useRef, useEffect } from "react";
import { ChevronDown, Search, Check, X } from "lucide-react";

export interface Option {
  id: string;
  name: string;
  color?: string;
}

interface MultiSearchableSelectProps {
  options: Option[];
  values: string[];
  onChange: (ids: string[]) => void;
  placeholder?: string;
  isRole?: boolean;
}

export default function MultiSearchableSelect({ options, values, onChange, placeholder = "Chọn nhiều...", isRole = false }: MultiSearchableSelectProps) {
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

  const selectedOptions = options.filter(opt => values.includes(opt.id));

  const getColorHex = (colorInt: string | undefined) => {
    if (!colorInt || colorInt === "0") return null;
    const hex = parseInt(colorInt).toString(16).padStart(6, '0');
    return `#${hex}`;
  };

  const handleToggleOption = (id: string) => {
    if (values.includes(id)) {
      onChange(values.filter(v => v !== id));
    } else {
      onChange([...values, id]);
    }
  };

  const handleRemove = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    onChange(values.filter(v => v !== id));
  };

  return (
    <div className="relative w-full" ref={wrapperRef}>
      <div 
        className="flex items-center justify-between w-full min-h-[42px] bg-surface border border-border text-sm rounded-lg px-3 py-2 text-white cursor-pointer hover:border-primary transition-colors"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex flex-wrap items-center gap-2 overflow-hidden w-full pr-4">
          {selectedOptions.length > 0 ? (
            selectedOptions.map(opt => {
              const color = getColorHex(opt.color);
              return (
                <div key={opt.id} className="flex items-center gap-1 bg-background px-2 py-1 rounded-md text-xs border border-border">
                  {isRole && color && <div className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />}
                  <span>{isRole ? `@${opt.name}` : `#${opt.name}`}</span>
                  <X className="w-3 h-3 cursor-pointer hover:text-red-400" onClick={(e) => handleRemove(e, opt.id)} />
                </div>
              );
            })
          ) : (
            <span className="text-text-muted">{placeholder}</span>
          )}
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
                const isSelected = values.includes(opt.id);
                return (
                  <div 
                    key={opt.id}
                    className={`px-3 py-2 text-sm cursor-pointer hover:bg-primary/20 flex items-center justify-between ${isSelected ? 'bg-primary/10 text-primary' : 'text-white'}`}
                    onClick={() => {
                      handleToggleOption(opt.id);
                      setSearchTerm("");
                    }}
                  >
                    <div className="flex items-center gap-2 truncate pr-2">
                      {isRole && color && (
                         <div className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: color }} />
                      )}
                      <span className="truncate">{isRole ? `@${opt.name}` : `#${opt.name}`}</span>
                    </div>
                    {isSelected && <Check className="w-4 h-4 shrink-0" />}
                  </div>
                );
              })
            ) : (
              <div className="px-3 py-4 text-center text-sm text-text-muted">
                Không tìm thấy kết quả
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
