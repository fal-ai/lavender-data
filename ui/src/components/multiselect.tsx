'use client';

import * as React from 'react';
import { Check, ChevronsUpDown, GripVertical } from 'lucide-react';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';

export type MultiSelectItem = {
  label: string;
  value: string;
  selected: boolean;
};

type MultiSelectProps = {
  value: MultiSelectItem[];
  onChange: (value: MultiSelectItem[]) => void;
  draggable?: boolean;
  label?: string;
  placeholder?: string;
  emptyText?: string;
  className?: string;
  singleSelect?: boolean;
};

export function MultiSelect({
  value,
  onChange,
  draggable = false,
  label = '',
  placeholder = '',
  emptyText = '',
  className = '',
  singleSelect = false,
}: MultiSelectProps) {
  const [open, setOpen] = React.useState(false);
  const [draggingItem, setDraggingItem] =
    React.useState<MultiSelectItem | null>(null);
  const handleDragStart = (item: MultiSelectItem) => {
    setDraggingItem(item);
  };
  const handleDragOver = (e: any) => {
    e.preventDefault();
  };
  const handleDrop = (e: any, targetItem: any) => {
    e.preventDefault();
    if (draggingItem) {
      const updatedItems = [...value];
      const draggingIndex = updatedItems.findIndex(
        (item) => item.value === draggingItem.value
      );
      const targetIndex = updatedItems.findIndex(
        (item) => item.value === targetItem.value
      );
      if (draggingIndex > targetIndex) {
        for (let i = draggingIndex; i > targetIndex; i--) {
          updatedItems[i] = updatedItems[i - 1];
        }
        updatedItems[targetIndex] = draggingItem;
      } else {
        for (let i = draggingIndex; i < targetIndex; i++) {
          updatedItems[i] = updatedItems[i + 1];
        }
        updatedItems[targetIndex] = draggingItem;
      }
      onChange(updatedItems);
      setDraggingItem(null);
    }
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className={cn('w-[200px] justify-between', className)}
        >
          {label}
          <ChevronsUpDown className="opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-full p-0">
        <Command>
          <CommandInput placeholder={placeholder} className="h-9" />
          <CommandList className="max-h-[480px]">
            <CommandEmpty>{emptyText}</CommandEmpty>
            <CommandGroup>
              {value.map((option) => (
                <CommandItem
                  key={option.value}
                  value={option.value}
                  onSelect={(currentValue) => {
                    const index = value.findIndex(
                      (v) => v.value === currentValue
                    );
                    if (index !== -1) {
                      const updatedItems = [...value];
                      updatedItems[index].selected =
                        !updatedItems[index].selected;
                      onChange(updatedItems);
                    }
                  }}
                  disabled={
                    singleSelect &&
                    value.filter((v) => v.selected).length > 0 &&
                    !option.selected
                  }
                  draggable={draggable}
                  onDragStart={() => handleDragStart(option)}
                  onDragOver={handleDragOver}
                  onDrop={(e) => handleDrop(e, option)}
                >
                  {draggable ? <GripVertical className="w-4 h-4" /> : <></>}
                  {option.label}
                  <Check
                    className={cn(
                      'ml-auto',
                      value.find((v) => v.value === option.value)?.selected
                        ? 'opacity-100'
                        : 'opacity-0'
                    )}
                  />
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
