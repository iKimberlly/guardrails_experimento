let currentUserId = null;


// ============================================================
// ELEMENTOS
// ============================================================

const userSelect =
    document.getElementById("userSelect");

const selectUserBtn =
    document.getElementById("selectUserBtn");

const userStatus =
    document.getElementById("userStatus");

const vehiclesSection =
    document.getElementById("vehiclesSection");

const securitySection =
    document.getElementById("securitySection");

const promptSection =
    document.getElementById("promptSection");

const vehiclesContainer =
    document.getElementById("vehiclesContainer");

const vehicleSummary =
    document.getElementById("vehicleSummary");

const reloadVehiclesBtn =
    document.getElementById("reloadVehiclesBtn");

const promptInput =
    document.getElementById("promptInput");

const testPromptBtn =
    document.getElementById("testPromptBtn");


// ============================================================
// CARREGAR USUÁRIOS
// ============================================================

async function loadUsers() {

    try {

        const response =
            await fetch("/users");

        if (!response.ok) {
            throw new Error(
                "Erro ao carregar usuários."
            );
        }

        const data =
            await response.json();

        userSelect.innerHTML =
            '<option value="">Selecione...</option>';

        data.users.forEach(user => {

            const option =
                document.createElement("option");

            option.value = user.id;

            option.textContent =
                `${user.id} - ${user.nome}`;

            userSelect.appendChild(option);

        });

    } catch (error) {

        console.error(error);

        userSelect.innerHTML =
            '<option value="">Erro ao carregar</option>';
    }
}


// ============================================================
// SELECIONAR USUÁRIO
// ============================================================

selectUserBtn.addEventListener(
    "click",
    async () => {

        const selectedId =
            userSelect.value;

        if (!selectedId) {

            showUserStatus(
                "Selecione um usuário.",
                "error"
            );

            return;
        }

        currentUserId =
            Number(selectedId);

        await loadUserData();

    }
);


// ============================================================
// CARREGAR DADOS DO USUÁRIO
// ============================================================

async function loadUserData() {

    try {

        const response =
            await fetch(
                "/my/vehicles",
                {
                    headers: {
                        "X-User-ID":
                            String(currentUserId)
                    }
                }
            );

        if (!response.ok) {

            const errorData =
                await response.json();

            throw new Error(
                errorData.detail ||
                "Erro ao consultar dados."
            );
        }

        const data =
            await response.json();


        // ----------------------------------------
        // STATUS
        // ----------------------------------------

        showUserStatus(
            `Usuário ${data.usuario.id} autenticado para o experimento. ` +
            `Acesso restrito aos próprios dados.`,
            "success"
        );


        // ----------------------------------------
        // MOSTRAR SEÇÕES
        // ----------------------------------------

        vehiclesSection.classList.remove(
            "hidden"
        );

        securitySection.classList.remove(
            "hidden"
        );

        promptSection.classList.remove(
            "hidden"
        );


        // ----------------------------------------
        // RESUMO
        // ----------------------------------------

        vehicleSummary.textContent =
            `${data.total} veículo(s) pertencente(s) ao usuário ${currentUserId}.`;


        // ----------------------------------------
        // TABELA
        // ----------------------------------------

        renderVehicles(
            data.veiculos
        );

    } catch (error) {

        console.error(error);

        showUserStatus(
            error.message,
            "error"
        );
    }
}


// ============================================================
// RENDERIZAR VEÍCULOS
// ============================================================

function renderVehicles(vehicles) {

    if (!vehicles.length) {

        vehiclesContainer.innerHTML =
            "<p>Nenhum veículo encontrado.</p>";

        return;
    }


    let html = `
        <div class="table-wrapper">

            <table>

                <thead>

                    <tr>
                        <th>ID</th>
                        <th>Categoria</th>
                        <th>Placa</th>
                        <th>Marca</th>
                        <th>Modelo</th>
                        <th>Ano</th>
                        <th>Cidade</th>
                        <th>Status</th>
                    </tr>

                </thead>

                <tbody>
    `;


    vehicles.forEach(vehicle => {

        html += `
            <tr>

                <td>
                    ${vehicle.id}
                </td>

                <td>
                    ${vehicle.categoria}
                </td>

                <td>
                    ${vehicle.placa}
                </td>

                <td>
                    ${vehicle.marca}
                </td>

                <td>
                    ${vehicle.modelo}
                </td>

                <td>
                    ${vehicle.ano}
                </td>

                <td>
                    ${vehicle.cidade}
                </td>

                <td>
                    ${vehicle.status}
                </td>

            </tr>
        `;

    });


    html += `
                </tbody>

            </table>

        </div>
    `;


    vehiclesContainer.innerHTML =
        html;
}


// ============================================================
// ATUALIZAR VEÍCULOS
// ============================================================

reloadVehiclesBtn.addEventListener(
    "click",
    async () => {

        if (!currentUserId) {
            return;
        }

        await loadUserData();

    }
);


// ============================================================
// STATUS DO USUÁRIO
// ============================================================

function showUserStatus(
    message,
    type
) {

    userStatus.textContent =
        message;

    userStatus.classList.remove(
        "hidden",
        "success",
        "error"
    );

    userStatus.classList.add(
        type
    );
}


// ============================================================
// BOTÕES DE TESTE RÁPIDO
// ============================================================

document
    .querySelectorAll(
        "[data-prompt]"
    )
    .forEach(button => {

        button.addEventListener(
            "click",
            () => {

                promptInput.value =
                    button.dataset.prompt;

            }
        );

    });


// ============================================================
// TESTAR PROMPT
// ============================================================

testPromptBtn.addEventListener(
    "click",
    async () => {

        const prompt =
            promptInput.value.trim();


        if (!prompt) {

            alert(
                "Digite um prompt."
            );

            return;
        }


        if (!currentUserId) {

            alert(
                "Selecione primeiro um usuário."
            );

            return;
        }


        testPromptBtn.disabled =
            true;

        testPromptBtn.textContent =
            "Testando...";


        try {

            const requestBody = {
                prompt: prompt
            };


            const headers = {
                "Content-Type":
                    "application/json",

                "X-User-ID":
                    String(currentUserId)
            };


            const [
                regexResponse,
                agentResponse,
                combinedResponse
            ] = await Promise.all([

                fetch(
                    "/validate/regex",
                    {
                        method: "POST",
                        headers: headers,
                        body:
                            JSON.stringify(
                                requestBody
                            )
                    }
                ),

                fetch(
                    "/validate/agent",
                    {
                        method: "POST",
                        headers: headers,
                        body:
                            JSON.stringify(
                                requestBody
                            )
                    }
                ),

                fetch(
                    "/validate/combined",
                    {
                        method: "POST",
                        headers: headers,
                        body:
                            JSON.stringify(
                                requestBody
                            )
                    }
                )

            ]);


            const regex =
                await regexResponse.json();

            const agent =
                await agentResponse.json();

            const combined =
                await combinedResponse.json();


            renderResult(
                "regexResult",
                regex
            );

            renderResult(
                "agentResult",
                agent
            );

            renderResult(
                "combinedResult",
                combined
            );


        } catch (error) {

            console.error(error);

            alert(
                "Erro ao executar o teste."
            );

        } finally {

            testPromptBtn.disabled =
                false;

            testPromptBtn.textContent =
                "Testar Prompt";

        }

    }
);


// ============================================================
// RENDERIZAR RESULTADO DO GUARDRAIL
// ============================================================

function renderResult(
    elementId,
    result
) {

    const element =
        document.getElementById(
            elementId
        );


    const status =
        result.approved
            ? "PERMITIDO"
            : "BLOQUEADO";


    let html = `
        <div class="result-status">

            <strong>
                ${status}
            </strong>

        </div>

        <p>
            <strong>Latência:</strong>
            ${result.latency_ms ?? "-"} ms
        </p>
    `;


    if (result.layer) {

        html += `
            <p>
                <strong>Camada:</strong>
                ${result.layer}
            </p>
        `;

    }


    if (
        result.matched_rules &&
        result.matched_rules.length
    ) {

        html += `
            <p>
                <strong>Regras:</strong>
                ${result.matched_rules.join(", ")}
            </p>
        `;

    }


    if (
        result.reasons &&
        result.reasons.length
    ) {

        html += `
            <p>
                <strong>Motivos:</strong>
                ${result.reasons.join("; ")}
            </p>
        `;

    }


    element.innerHTML =
        html;
}


// ============================================================
// INICIALIZAÇÃO
// ============================================================

loadUsers();