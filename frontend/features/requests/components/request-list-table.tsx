"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { Search } from "lucide-react";

import { EmptyState } from "@/components/empty-state";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { RequestStatusBadge } from "@/features/requests/status-badges";
import { interpolate, useI18n } from "@/i18n/hooks";
import type { RequestRecord } from "@/lib/api/types";
import { formatDateTime } from "@/lib/utils";

export function RequestListTable({ requests }: { requests: RequestRecord[] }) {
  const [globalFilter, setGlobalFilter] = useState("");
  const { locale, messages } = useI18n();

  const columns = useMemo<ColumnDef<RequestRecord>[]>(
    () => [
      {
        accessorKey: "title",
        header: messages.requests.list.columns.title,
        cell: ({ row }) => (
          <div className="space-y-1">
            <p className="font-semibold tracking-[-0.01em] text-slate-900">
              {row.original.title}
            </p>
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-slate-500">
              {messages.requests.sources[row.original.source]}
            </p>
          </div>
        ),
      },
      {
        accessorKey: "status",
        header: messages.requests.list.columns.status,
        cell: ({ row }) => <RequestStatusBadge status={row.original.status} />,
      },
      {
        id: "documents",
        header: messages.requests.list.columns.documents,
        cell: () => (
          <span className="text-sm font-medium text-slate-400">
            -
          </span>
        ),
      },
      {
        accessorKey: "updated_at",
        header: messages.requests.list.columns.updated,
        cell: ({ row }) => (
          <span className="text-sm font-medium text-slate-700">
            {formatDateTime(row.original.updated_at, locale)}
          </span>
        ),
      },
      {
        id: "actions",
        header: messages.requests.list.columns.actions,
        cell: ({ row }) => (
          <Link
            href={`/requests/${row.original.id}`}
            className="focus-ring inline-flex h-9 items-center justify-center rounded-[var(--radius-control)] px-3 text-xs font-semibold uppercase tracking-[0.14em] text-slate-700 transition hover:bg-surfaceMuted"
          >
            {messages.requests.list.open}
          </Link>
        ),
      },
    ],
    [locale, messages],
  );

  const table = useReactTable({
    data: requests,
    columns,
    state: {
      globalFilter,
    },
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    globalFilterFn: (row, _columnId, filterValue) => {
      const query = String(filterValue).toLowerCase();
      return (
        row.original.title.toLowerCase().includes(query) ||
        row.original.status.toLowerCase().includes(query)
      );
    },
  });

  if (!requests.length) {
    return (
      <EmptyState
        title={messages.requests.list.emptyTitle}
        description={messages.requests.list.emptyDescription}
        action={{ label: messages.requests.list.emptyAction, href: "/requests/new" }}
      />
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="eyebrow">
            {messages.requests.list.eyebrow}
          </p>
          <div className="mt-2 flex flex-wrap items-center gap-3">
            <CardTitle>{messages.requests.list.title}</CardTitle>
            <Badge variant="neutral" size="sm">
              {interpolate(messages.requests.list.records, { count: requests.length })}
            </Badge>
          </div>
          <p className="mt-2 text-sm text-slate-600">
            {messages.requests.list.description}
          </p>
        </div>
        <div className="relative w-full max-w-sm">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <Input
            value={globalFilter}
            onChange={(event) => setGlobalFilter(event.target.value)}
            placeholder={messages.requests.list.searchPlaceholder}
            className="pl-10"
          />
        </div>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead
                    key={header.id}
                    className={header.column.id === "actions" ? "text-right" : undefined}
                  >
                    {header.isPlaceholder
                      ? null
                      : flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.map((row) => (
              <TableRow key={row.id}>
                {row.getVisibleCells().map((cell) => (
                  <TableCell
                    key={cell.id}
                    className={cell.column.id === "actions" ? "text-right" : undefined}
                  >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
