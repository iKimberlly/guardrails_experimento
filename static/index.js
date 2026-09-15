const promptInput = document.getElementById("prompt");

const testButton = document.getElementById("testButton");

const clearButton = document.getElementById("clearButton");

const results = document.getElementById("results");

const loading = document.getElementById("loading");


/* =========================
   TESTAR PROMPT
========================= */

testButton.addEventListener("click", async () => {

    const prompt = promptInput.value.trim();

    if (!prompt) {

        alert("Digite um prompt antes de testar.");

        return;
    }


    loading.classList.remove("hidden");

    results.classList.add("hidden");

    testButton.disabled = true;


    try {

        const [regex, agent, combined] = await Promise.all([

            callAPI("/validate/regex", prompt),

            callAPI("/validate/agent", prompt),

            callAPI("/validate/combined", prompt)

        ]);


        displayResult("regex", regex);

        displayResult("agent", agent);

        displayResult("combined", combined);


        results.classList.remove("hidden");

    }

    catch (error) {

        console.error(error);

        alert(
            "Erro ao testar o prompt.\n\n" +
            error.message
        );

    }

    finally {

        loading.classList.add("hidden");

        testButton.disabled = false;

    }

});


/* =========================
   CHAMAR API
========================= */

async function callAPI(endpoint, prompt) {

    const response = await fetch(endpoint, {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            prompt: prompt
        })

    });


    if (!response.ok) {

        const text = await response.text();

        throw new Error(
            `${endpoint}: ${response.status} - ${text}`
        );

    }


    return await response.json();

}


/* =========================
   MOSTRAR RESULTADO
========================= */

function displayResult(type, data) {

    const status = document.getElementById(
        `${type}-status`
    );

    const latency = document.getElementById(
        `${type}-latency`
    );

    const layer = document.getElementById(
        `${type}-layer`
    );

    const reasons = document.getElementById(
        `${type}-reasons`
    );


    /* STATUS */

    if (data.approved) {

        status.textContent = "APROVADO";

        status.className = "badge approved";

    }

    else {

        status.textContent = "BLOQUEADO";

        status.className = "badge blocked";

    }


    /* LATÊNCIA */

    if (data.latency_ms !== undefined) {

        latency.textContent =
            `${Number(data.latency_ms).toFixed(2)} ms`;

    }

    else {

        latency.textContent = "-";

    }


    /* CAMADA */

    if (layer) {

        layer.textContent =
            data.layer || "-";

    }


    /* REASONS */

    if (reasons) {

        if (
            Array.isArray(data.reasons) &&
            data.reasons.length > 0
        ) {

            reasons.textContent =
                data.reasons.join(", ");

        }

        else {

            reasons.textContent =
                "Nenhum motivo informado.";

        }

    }


    /* REGRAS */

    const rules = document.getElementById(
        `${type}-rules`
    );

    if (rules) {

        if (
            Array.isArray(data.matched_rules) &&
            data.matched_rules.length > 0
        ) {

            rules.textContent =
                data.matched_rules.join(", ");

        }

        else {

            rules.textContent = "Nenhuma";

        }

    }


    /* MODELO DO AGENT */

    if (type === "agent") {

        const model =
            document.getElementById("agent-model");

        model.textContent =
            data.agent_model || "-";

    }


    /* PROMPT SANITIZADO */

    const sanitized =
        document.getElementById("sanitized-prompt");

    if (
        data.sanitized_prompt &&
        type === "combined"
    ) {

        sanitized.textContent =
            data.sanitized_prompt;

    }

}


/* =========================
   LIMPAR
========================= */

clearButton.addEventListener("click", () => {

    promptInput.value = "";

    results.classList.add("hidden");

    promptInput.focus();

});


/* =========================
   TESTES RÁPIDOS
========================= */

document
    .querySelectorAll(".quick-btn")
    .forEach(button => {

        button.addEventListener("click", () => {

            promptInput.value =
                button.dataset.prompt;

            promptInput.focus();

        });

    });