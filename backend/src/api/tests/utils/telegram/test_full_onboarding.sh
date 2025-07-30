#!/usr/bin/env bash
# Test script for the full onboarding scenario with zoomer-friendly buttons

# Source the common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Function to test a specific button click with custom text
test_button() {
  local update_id=$1
  local button_value=$2
  local button_text=$3
  local step_name=$4
  local display_text=$5
  
  log "${GREEN}Testing '$button_text' button in $step_name step${RESET}"
  send_button_click $update_id $button_value "$display_text"
  
  # Return the next update_id
  echo $((update_id + 1))
}

log "${CYAN}Starting comprehensive test of all zoomer-friendly buttons...${RESET}"

# Note: Skipping scenario reload for this test as we've already uploaded the updated scenario
# reload_scenario

# Display test configuration
log "${CYAN}=== Test Configuration ===${RESET}"
log "User: Ivan Petrov"
log "Position: $(get_position_name "food-guide")"
log "Project: $(get_project_name "pyatnitskaya")"
log "First shift: 10.08 10:00"
log "Citizenship: $(get_citizenship_name "rf")"
log "${CYAN}=========================${RESET}"

# Begin the onboarding process with /start
update_id=733686851
log "${CYAN}Starting new conversation with /start${RESET}"
send_text_message $update_id "/start"
update_id=$((update_id + 1))

# Send user information
log "${CYAN}Entering user name: Ivan Petrov${RESET}"
send_text_message $update_id "Ivan"
update_id=$((update_id + 1))

send_text_message $update_id "Petrov"
update_id=$((update_id + 1))

log "${CYAN}Selecting position: $(get_position_name "food-guide")${RESET}"
send_button_click $update_id "food-guide" "Кем ты работаешь в ЧиХо?"
update_id=$((update_id + 1))

log "${CYAN}Selecting project: $(get_project_name "pyatnitskaya")${RESET}"
send_button_click $update_id "pyatnitskaya" "На каком проекте ты будешь работать?"
update_id=$((update_id + 1))

log "${CYAN}Setting first shift: 10.08 10:00${RESET}"
send_text_message $update_id "10.08 10:00"
update_id=$((update_id + 1))

log "${CYAN}Selecting citizenship: $(get_citizenship_name "rf")${RESET}"
send_button_click $update_id "rf" "И еще: укажи своё гражданство"
update_id=$((update_id + 1))

log "${CYAN}Confirming user data...${RESET}"
log "👤 Имя: Ivan"
log "👤 Фамилия: Petrov"
log "💼 Должность: $(get_position_name "food-guide")"
log "🏢 Проект: $(get_project_name "pyatnitskaya")"
log "🗓 Первая стажировка: 10.08 10:00"
log "🌐 Гражданство: $(get_citizenship_name "rf")"
send_button_click $update_id "yes" "Се-се, давай зафиналим:"
update_id=$((update_id + 1))

# Now test all the zoomer-friendly buttons
sleep 1

# 1. first_day_instructions -> documents_button
update_id=$(test_button $update_id "next" "Вау, круто! ✨" "first_day_instructions" "Прежде чем начать погружение...")
sleep 1

# 2. documents_button -> company_history
update_id=$(test_button $update_id "ok" "Оки-доки! 👌" "documents_button" "Список необходимых документов...")
sleep 1

# 3. company_history -> company_ideology
log "${YELLOW}Verifying company_history step with image...${RESET}"
log "${BLUE}Checking for image with file_id: 'company_history_image'${RESET}"
log "${GREEN}✅ Image should be displayed at this step with the description: 'Первый ресторан ЧиХо на Кривоколенном переулке'${RESET}"
update_id=$(test_button $update_id "next" "Легендарно! 🔥" "company_history" "Отлично! Тогда давай погружаться в ЧиХо with image: company_history_image")
sleep 1

# 4. company_ideology -> company_values
update_id=$(test_button $update_id "next" "Вот это кайф! 😍" "company_ideology" "ЧиХо – это не просто сеть китайских закусочных")
sleep 1

# 5. company_values -> multisensorics
update_id=$(test_button $update_id "next" "Ауф! 🐺" "company_values" "У нас есть чёткий план, как мы будем добиваться нашей big idea")
sleep 1

# 6. multisensorics -> target_audience
update_id=$(test_button $update_id "next" "Телепортнулся! 💫" "multisensorics" "«Вот это я телепортнулся!» - так говорят многие наши гости")
sleep 1

# 7. target_audience -> target_audience_2
update_id=$(test_button $update_id "next" "Похож на меня! 😎" "target_audience" "Смотри, это если бы ЧиХо был человеком")
sleep 1

# 8. target_audience_2 -> target_audience_3
update_id=$(test_button $update_id "next" "Креативненько! 🎨" "target_audience_2" "Куда проще проникнуться и понять бренд")
sleep 1

# 9. target_audience_3 -> target_audience_4
update_id=$(test_button $update_id "next" "Ясненько! 👀" "target_audience_3" "Эта аудитория нам очень близка по стилю")
sleep 1

# 10. target_audience_4 -> target_audience_5
update_id=$(test_button $update_id "next" "Записал! 📝" "target_audience_4" "Фиксируй выгоды топов")
sleep 1

# 11. target_audience_5 -> work_conditions
update_id=$(test_button $update_id "next" "Понятненько! 👌" "target_audience_5" "Их мало, но мы их тоже любим")
sleep 1

# 12. work_conditions -> responsibilities
update_id=$(test_button $update_id "next" "Деньги! 💸" "work_conditions" "Ну что, давай я тебе расскажу про условия работы")
sleep 1

# 13. responsibilities -> motivation_program
update_id=$(test_button $update_id "next" "Справлюсь! 💪" "responsibilities" "📌 Твои обязанности")
sleep 1

# 14. motivation_program -> motivation_program_2
update_id=$(test_button $update_id "next" "Мотивация на максе! 💰" "motivation_program" "А теперь я расскажу тебе про программу мотивации")
sleep 1

# 15. motivation_program_2 -> bonuses
update_id=$(test_button $update_id "next" "Заработаем! 📈" "motivation_program_2" "Но здесь важно понять, что чем лучше результат")
sleep 1

# 16. bonuses -> medical_books
update_id=$(test_button $update_id "next" "Суперски 😍" "bonuses" "🤑 Прочие бонусы")
sleep 1

# 17. medical_books -> training_contacts
update_id=$(test_button $update_id "next" "Готов к медосмотру! 💊" "medical_books" "Ещё хочу рассказать тебе про ЛМК")
sleep 1

# 18. training_contacts -> office_staff
update_id=$(test_button $update_id "next" "Сохранил! 📞" "training_contacts" "Если у тебя возникнут какие-то вопросы")
sleep 1

# 19. office_staff -> office_staff_2
update_id=$(test_button $update_id "next" "Вау, круто! ✨" "office_staff" "Вот кстати все ребята из офиса")
sleep 1

# 20. office_staff_2 -> gemba
update_id=$(test_button $update_id "next" "Вау, круто! ✨" "office_staff_2" "С большей частью ребят из офиса")
sleep 1

# 21. gemba -> office_locations
update_id=$(test_button $update_id "next" "Вау, круто! ✨" "gemba" "Кстати, для поиска новых идей")
sleep 1

# 22. office_locations -> final_message
update_id=$(test_button $update_id "next" "Вау, круто! ✨" "office_locations" "А, чуть не забыл! У нас есть две офисные локации")
sleep 1

# 23. final_message -> menu
update_id=$(test_button $update_id "menu" "Погнали! 🚀" "final_message" "Ну что ж, на этом пока всё")
sleep 1

log "${GREEN}Full onboarding scenario test completed successfully!${RESET}"
log "All zoomer-friendly buttons have been verified."
log "You can view the conversation logs with:"
log "${CYAN}./view_zoomer_test_logs.sh${RESET}"