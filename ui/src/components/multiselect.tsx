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

type Item = {
  label: string;
  value: string;
};

type MultiSelectProps = {
  options: Item[];
  value: string[];
  setValue: React.Dispatch<React.SetStateAction<string[]>>;
  setOptions?: React.Dispatch<React.SetStateAction<Item[]>>;
  draggable?: boolean;
  label?: string;
  placeholder?: string;
  emptyText?: string;
  className?: string;
};

export function MultiSelect({
  options,
  value,
  setValue,
  setOptions = () => {},
  draggable = false,
  label = '',
  placeholder = '',
  emptyText = '',
}: MultiSelectProps) {
  const [open, setOpen] = React.useState(false);
  const [draggingItem, setDraggingItem] = React.useState<Item | null>(null);
  const handleDragStart = (item: Item) => {
    setDraggingItem(item);
  };
  const handleDragOver = (e: any) => {
    e.preventDefault();
  };
  const handleDrop = (e: any, targetItem: any) => {
    e.preventDefault();
    if (draggingItem) {
      setOptions((prev: Item[]) => {
        const updatedItems = [...prev];
        const draggingIndex = updatedItems.findIndex(
          (item) => item.value === draggingItem.value
        );
        const targetIndex = updatedItems.findIndex(
          (item) => item.value === targetItem.value
        );
        [updatedItems[draggingIndex], updatedItems[targetIndex]] = [
          updatedItems[targetIndex],
          updatedItems[draggingIndex],
        ];
        return updatedItems;
      });
      setValue((prev: string[]) => {
        const updatedItems = [...prev];
        const draggingIndex = updatedItems.findIndex(
          (item) => item === draggingItem.value
        );
        const targetIndex = updatedItems.findIndex(
          (item) => item === targetItem.value
        );
        [updatedItems[draggingIndex], updatedItems[targetIndex]] = [
          updatedItems[targetIndex],
          updatedItems[draggingIndex],
        ];
        return updatedItems;
      });
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
          className="w-[200px] justify-between"
        >
          {label}
          <ChevronsUpDown className="opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[200px] p-0">
        <Command>
          <CommandInput placeholder={placeholder} className="h-9" />
          <CommandList>
            <CommandEmpty>{emptyText}</CommandEmpty>
            <CommandGroup>
              {options.map((option) => (
                <CommandItem
                  key={option.value}
                  value={option.value}
                  onSelect={(currentValue) => {
                    setValue(
                      value.includes(currentValue)
                        ? value.filter((v) => v !== currentValue)
                        : [...value, currentValue]
                    );
                  }}
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
                      value.includes(option.value) ? 'opacity-100' : 'opacity-0'
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
