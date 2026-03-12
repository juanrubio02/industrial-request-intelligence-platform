import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { useI18n } from "@/i18n/hooks";
import { I18nProvider } from "@/i18n/provider";

function Probe() {
  const { locale, messages, setLocale } = useI18n();

  return (
    <div>
      <p>{locale}</p>
      <p>{messages.requests.header.title}</p>
      <button type="button" onClick={() => setLocale("en")}>
        change
      </button>
    </div>
  );
}

describe("I18nProvider", () => {
  it("starts in spanish and persists a locale change", async () => {
    const user = userEvent.setup();

    render(
      <I18nProvider initialLocale="es">
        <Probe />
      </I18nProvider>,
    );

    expect(screen.getByText("es")).toBeInTheDocument();
    expect(screen.getByText("Solicitudes")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "change" }));

    expect(screen.getByText("en")).toBeInTheDocument();
    expect(screen.getByText("Requests")).toBeInTheDocument();
    expect(window.localStorage.getItem("iri.locale")).toBe("en");
    expect(document.cookie).toContain("iri.locale=en");
  });
});
