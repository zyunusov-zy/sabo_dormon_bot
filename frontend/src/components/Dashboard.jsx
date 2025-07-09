import React, { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";

const mockData = [
  { id: 1, name: "Иван Петров", date: "2025-07-01", status: "Approved" },
  { id: 2, name: "Мария Сидорова", date: "2025-07-02", status: "Rejected" },
  { id: 3, name: "Алексей Козлов", date: "2025-07-03", status: "Pending" },
];

const StatusBadge = ({ status }) => {
  const statusText = {
    Approved: "Одобрено",
    Rejected: "Отклонено",
    Pending: "Ожидание",
  }[status];

  const color = {
    Approved: "bg-green-100 text-green-800",
    Rejected: "bg-red-100 text-red-800",
    Pending: "bg-yellow-100 text-yellow-800",
  }[status];

  return <Badge className={color}>{statusText}</Badge>;
};

const ActionButtons = ({ patient, onApprove, onReject }) => {
  if (patient.status !== "Pending") return null;

  return (
    <div className="flex gap-2">
      <Button
        size="sm"
        onClick={() => onApprove(patient.id)}
        className="bg-green-500 hover:bg-green-600 text-white"
      >
        Одобрить
      </Button>
      <Button
        size="sm"
        variant="outline"
        onClick={() => onReject(patient.id)}
        className="border-red-500 text-red-500 hover:bg-red-50"
      >
        Отклонить
      </Button>
    </div>
  );
};

const isLate = (dateStr, status) => {
  if (status !== "Pending") return false;
  const now = new Date();
  const date = new Date(dateStr);
  const diffDays = (now - date) / (1000 * 60 * 60 * 24);
  return diffDays > 3;
};

// SVG Icons
const TotalIcon = () => (
  <svg
    className="w-8 h-8 text-blue-500"
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
    />
  </svg>
);

const ApprovedIcon = () => (
  <svg
    className="w-8 h-8 text-green-500"
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
    />
  </svg>
);

const RejectedIcon = () => (
  <svg
    className="w-8 h-8 text-red-500"
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
    />
  </svg>
);

const PendingIcon = () => (
  <svg
    className="w-8 h-8 text-yellow-500"
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
    />
  </svg>
);

const LateIcon = () => (
  <svg
    className="w-8 h-8 text-orange-500"
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
    />
  </svg>
);

export default function Dashboard() {
  const [statusFilter, setStatusFilter] = useState("Все");
  const [search, setSearch] = useState("");
  const [viewMode, setViewMode] = useState("table");
  const [patients, setPatients] = useState(mockData);

  const handleApprove = (patientId) => {
    setPatients((prev) =>
      prev.map((p) => (p.id === patientId ? { ...p, status: "Approved" } : p))
    );
  };

  const handleReject = (patientId) => {
    setPatients((prev) =>
      prev.map((p) => (p.id === patientId ? { ...p, status: "Rejected" } : p))
    );
  };

  const filtered = patients.filter((p) => {
    const matchesStatus =
      statusFilter === "Все" ||
      (statusFilter === "Одобрено" && p.status === "Approved") ||
      (statusFilter === "Отклонено" && p.status === "Rejected") ||
      (statusFilter === "Ожидание" && p.status === "Pending");
    const matchesSearch = p.name.toLowerCase().includes(search.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  const total = patients.length;
  const approved = patients.filter((p) => p.status === "Approved").length;
  const rejected = patients.filter((p) => p.status === "Rejected").length;
  const pending = patients.filter((p) => p.status === "Pending").length;
  const late = patients.filter((p) => isLate(p.date, p.status)).length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-6">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            Панель управления пациентами
          </h1>
          <p className="text-gray-600">
            Управление и отслеживание заявок пациентов
          </p>
        </div>

        {/* Statistics Cards */}
        <div className="grid md:grid-cols-2 gap-4">
          {/* Main Statistics Card */}
          <Card className="bg-white shadow-md border hover:shadow-lg transition-shadow duration-200">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-800">
                  Статистика
                </h2>
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg">
                  <TotalIcon className="w-5 h-5 text-blue-600" />
                  <div>
                    <p className="text-xs text-gray-500">Всего</p>
                    <p className="text-xl font-bold text-blue-600">{total}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg">
                  <ApprovedIcon className="w-5 h-5 text-green-600" />
                  <div>
                    <p className="text-xs text-gray-500">Одобрено</p>
                    <p className="text-xl font-bold text-green-600">
                      {approved}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-3 bg-red-50 rounded-lg">
                  <RejectedIcon className="w-5 h-5 text-red-600" />
                  <div>
                    <p className="text-xs text-gray-500">Отклонено</p>
                    <p className="text-xl font-bold text-red-600">{rejected}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-3 bg-yellow-50 rounded-lg">
                  <PendingIcon className="w-5 h-5 text-yellow-600" />
                  <div>
                    <p className="text-xs text-gray-500">Ожидание</p>
                    <p className="text-xl font-bold text-yellow-600">
                      {pending}
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Late Requests Card */}
          <Card className="bg-gradient-to-br from-orange-500 to-red-500 text-white shadow-md border hover:shadow-lg transition-shadow duration-200">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Просрочки</h2>
                <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
              </div>

              <div className="flex items-center gap-4">
                <div className="bg-white/20 p-3 rounded-lg">
                  <LateIcon className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-sm opacity-90">Просроченные заявки</p>
                  <p className="text-2xl font-bold">{late}</p>
                  <p className="text-xs opacity-75 mt-1">Требует внимания</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filters and Controls */}
        <Card className="bg-white shadow-lg border-0">
          <CardContent className="p-1">
            <div className="flex flex-wrap gap-4 items-center justify-between">
              <div className="flex gap-4 items-center">
                <Input
                  placeholder="Поиск пациентов..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="max-w-sm border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                />
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="outline"
                      className="border-gray-300 hover:bg-gray-50"
                    >
                      Фильтр: {statusFilter}
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent>
                    {["Все", "Одобрено", "Отклонено", "Ожидание"].map((s) => (
                      <DropdownMenuItem
                        key={s}
                        onClick={() => setStatusFilter(s)}
                      >
                        {s}
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>

              <div className="flex gap-2">
                <Button
                  variant={viewMode === "table" ? "default" : "outline"}
                  onClick={() => setViewMode("table")}
                  className={
                    viewMode === "table"
                      ? "bg-blue-500 hover:bg-blue-600"
                      : "border-gray-300 hover:bg-gray-50"
                  }
                >
                  Таблица
                </Button>
                <Button
                  variant={viewMode === "cards" ? "default" : "outline"}
                  onClick={() => setViewMode("cards")}
                  className={
                    viewMode === "cards"
                      ? "bg-blue-500 hover:bg-blue-600"
                      : "border-gray-300 hover:bg-gray-50"
                  }
                >
                  Карточки
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Data View */}
        {viewMode === "table" ? (
          <Card className="bg-white shadow-lg border-0">
            <div className="overflow-hidden">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-4 text-left font-semibold text-gray-700">
                      Имя
                    </th>
                    <th className="px-6 py-4 text-left font-semibold text-gray-700">
                      Дата заявки
                    </th>
                    <th className="px-6 py-4 text-left font-semibold text-gray-700">
                      Статус
                    </th>
                    <th className="px-6 py-4 text-left font-semibold text-gray-700">
                      Действия
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {filtered.map((p) => (
                    <tr
                      key={p.id}
                      className="hover:bg-gray-50 transition-colors"
                    >
                      <td className="px-6 py-4 font-medium text-gray-900">
                        {p.name}
                      </td>
                      <td className="px-6 py-4 text-gray-600">{p.date}</td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <StatusBadge status={p.status} />
                          {isLate(p.date, p.status) && (
                            <span className="text-orange-500 font-medium">
                              ⚠️ Просрочено
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <ActionButtons
                          patient={p}
                          onApprove={handleApprove}
                          onReject={handleReject}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {filtered.map((p) => (
              <Card
                key={p.id}
                className="bg-white shadow-lg border-0 hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
              >
                <CardContent className="p-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xl font-bold text-gray-800">
                      {p.name}
                    </h3>
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  </div>
                  <p className="text-gray-600 font-medium">{p.date}</p>
                  <div className="flex items-center justify-between">
                    <StatusBadge status={p.status} />
                    {isLate(p.date, p.status) && (
                      <span className="text-orange-500 font-medium text-sm">
                        ⚠️ Просрочено
                      </span>
                    )}
                  </div>
                  <ActionButtons
                    patient={p}
                    onApprove={handleApprove}
                    onReject={handleReject}
                  />
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
